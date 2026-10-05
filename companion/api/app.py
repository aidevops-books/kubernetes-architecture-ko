"""CloudShop teaching API. PostgreSQL in Kubernetes, explicit SQLite local test mode."""
import json
import os
import signal
import socket
import sqlite3
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

STOPPING = threading.Event()
COUNTERS = {"requests": 0, "errors": 0}
LOCK = threading.Lock()
SQLITE = os.environ.get("SQLITE_PATH")


def connect():
    if SQLITE:
        conn = sqlite3.connect(SQLITE, timeout=3)
        conn.execute("PRAGMA busy_timeout=3000")
        return conn
    import psycopg
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "postgres"),
        dbname=os.environ.get("DB_NAME", "cloudshop"),
        user=os.environ.get("DB_USER", "cloudshop"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=2, options="-c statement_timeout=2000",
    )


def execute(conn, sql, params=()):
    return conn.execute(sql.replace("%s", "?") if SQLITE else sql, params)


def initialize():
    conn = connect()
    try:
        execute(conn, "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL)")
        execute(conn, "CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, idem_key TEXT UNIQUE NOT NULL, product_id INTEGER NOT NULL REFERENCES products(id), quantity INTEGER NOT NULL CHECK (quantity > 0), created_at TEXT NOT NULL)")
        for row in [(1, "아키텍처 노트", 12000), (2, "클라우드 머그", 18000), (3, "네트워크 스티커", 3000)]:
            execute(conn, "INSERT INTO products (id,name,price) VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING", row)
        conn.commit()
    finally:
        conn.close()


def cache():
    host = os.environ.get("REDIS_HOST")
    if not host:
        return None
    import redis
    return redis.Redis(host=host, port=6379, socket_connect_timeout=.3, socket_timeout=.3, decode_responses=True)


class Handler(BaseHTTPRequestHandler):
    server_version = "CloudShop/0.1"

    def log_message(self, *_):
        pass

    def send(self, code, data, content_type="application/json; charset=utf-8"):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        payload = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Request-ID", self.rid)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            pass
        with LOCK:
            COUNTERS["requests"] += 1
            COUNTERS["errors"] += int(code >= 500)
        print(json.dumps({"request_id": self.rid, "method": self.command, "path": self.path.split('?')[0], "status": code, "duration_ms": round((time.monotonic()-self.started)*1000, 2), "instance": socket.gethostname()}, ensure_ascii=False), flush=True)

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        self.started = time.monotonic()
        self.rid = self.headers.get("X-Request-ID", str(uuid.uuid4()))[:100]
        path = self.path.split("?")[0]
        try:
            if self.command == "GET" and path == "/healthz":
                return self.send(200, {"alive": True})
            if self.command == "GET" and path == "/readyz":
                if STOPPING.is_set():
                    return self.send(503, {"ready": False})
                conn = connect()
                try:
                    execute(conn, "SELECT 1")
                finally:
                    conn.close()
                return self.send(200, {"ready": True})
            if self.command == "GET" and path == "/metrics":
                with LOCK:
                    values = dict(COUNTERS)
                return self.send(200, "".join(f"cloudshop_{k}_total {v}\n" for k, v in values.items()), "text/plain; charset=utf-8")
            if self.command == "GET" and path == "/api/info":
                return self.send(200, {"message": os.environ.get("APP_MESSAGE", "CloudShop"), "instance": socket.gethostname()})
            if self.command == "GET" and path in ("/api/shipping", "/api/description"):
                suffix = "/shipping" if path.endswith("shipping") else "/description"
                base = os.environ.get("EXTERNAL_URL", "http://external-mock:8080")
                try:
                    with urlopen(base+suffix, timeout=1.5) as response:
                        result = json.loads(response.read(16384))
                    return self.send(200, {"degraded": False, "result": result})
                except (URLError, TimeoutError, ValueError, OSError):
                    return self.send(200, {"degraded": True, "result": {"text": "현재 외부 정보를 가져올 수 없습니다. 기본 상품 정보를 확인해 주세요."}})
            if self.command == "GET" and path == "/api/products":
                redis_client = cache()
                if redis_client:
                    try:
                        stored = redis_client.get("cloudshop:products")
                        if stored:
                            return self.send(200, {"source": "cache", "products": json.loads(stored)})
                    except Exception:
                        pass  # Cache is optional; authoritative data remains in PostgreSQL.
                conn = connect()
                try:
                    rows = execute(conn, "SELECT id,name,price FROM products ORDER BY id").fetchall()
                finally:
                    conn.close()
                products = [dict(zip(("id", "name", "price"), row)) for row in rows]
                if redis_client:
                    try:
                        redis_client.setex("cloudshop:products", 30, json.dumps(products, ensure_ascii=False))
                    except Exception:
                        pass
                return self.send(200, {"source": "database", "products": products})
            if self.command == "POST" and path == "/api/orders":
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    return self.send(400, {"error": "body_length"})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    return self.send(400, {"error": "object_required"})
                product, quantity = data.get("product_id"), data.get("quantity")
                key = self.headers.get("Idempotency-Key", "")
                if not key or len(key) > 100 or type(product) is not int or type(quantity) is not int or not 1 <= quantity <= 100:
                    return self.send(400, {"error": "invalid_order_or_key"})
                conn = connect()
                try:
                    if not execute(conn, "SELECT id FROM products WHERE id=%s", (product,)).fetchone():
                        return self.send(404, {"error": "product_not_found"})
                    order_id = str(uuid.uuid4())
                    execute(conn, "INSERT INTO orders (id,idem_key,product_id,quantity,created_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (idem_key) DO NOTHING", (order_id, key, product, quantity, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
                    row = execute(conn, "SELECT id,product_id,quantity FROM orders WHERE idem_key=%s", (key,)).fetchone()
                    conn.commit()
                finally:
                    conn.close()
                if (row[1], row[2]) != (product, quantity):
                    return self.send(409, {"error": "idempotency_conflict"})
                return self.send(201 if row[0] == order_id else 200, {"order": dict(zip(("id", "product_id", "quantity"), row))})
            if self.command == "GET" and path.startswith("/api/orders/"):
                conn = connect()
                try:
                    row = execute(conn, "SELECT id,product_id,quantity FROM orders WHERE id=%s", (path.rsplit("/", 1)[-1],)).fetchone()
                finally:
                    conn.close()
                return self.send(200, {"order": dict(zip(("id", "product_id", "quantity"), row))}) if row else self.send(404, {"error": "order_not_found"})
            return self.send(404, {"error": "not_found"})
        except (ValueError, UnicodeError):
            return self.send(400, {"error": "invalid_input"})
        except Exception as exc:
            print(json.dumps({"request_id": self.rid, "error_type": type(exc).__name__}), flush=True)
            return self.send(503, {"error": "dependency_unavailable"})


def main():
    for attempt in range(30):
        try:
            initialize()
            break
        except Exception as exc:
            print(json.dumps({"phase": "initialize", "attempt": attempt+1, "error_type": type(exc).__name__}), flush=True)
            time.sleep(2)
    else:
        raise SystemExit("database initialization failed")
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler)
    server.daemon_threads = False

    def stop(*_):
        STOPPING.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
