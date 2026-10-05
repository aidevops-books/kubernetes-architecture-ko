"""Bounded educational request-rate generator; records generator queue delay."""
import argparse
import concurrent.futures
import json
import math
import time
import uuid
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--base", default="http://127.0.0.1:8080")
parser.add_argument("--rate", type=int, default=20)
parser.add_argument("--seconds", type=int, default=60)
args = parser.parse_args()
if not 1 <= args.rate <= 200 or not 1 <= args.seconds <= 300:
    parser.error("educational limits: rate 1..200 and seconds 1..300")


def one(i, scheduled):
    start = time.monotonic()
    write = i % 10 == 0
    request = Request(args.base+("/api/orders" if write else "/api/products"),
                      data=b'{"product_id":1,"quantity":1}' if write else None,
                      headers={"Content-Type": "application/json", "Idempotency-Key": str(uuid.uuid4())})
    ok = False
    try:
        with urlopen(request, timeout=5) as response:
            response.read()
            ok = 200 <= response.status < 300
    except Exception:
        pass
    end = time.monotonic()
    return ok, (end-scheduled)*1000, (start-scheduled)*1000, (end-start)*1000


start = time.monotonic()
pending = set()
rows = []
skipped = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
    for i in range(args.rate*args.seconds):
        scheduled = start+i/args.rate
        time.sleep(max(0, scheduled-time.monotonic()))
        done = {f for f in pending if f.done()}
        rows.extend(f.result() for f in done)
        pending -= done
        if len(pending) >= 64:
            skipped += 1
            continue
        pending.add(pool.submit(one, i, scheduled))
    rows.extend(f.result() for f in concurrent.futures.as_completed(pending))
elapsed = time.monotonic()-start


def p95(index):
    values = sorted(r[index] for r in rows)
    return round(values[max(0, math.ceil(len(values)*.95)-1)], 2) if values else None


print(json.dumps({"scheduled": args.rate*args.seconds, "completed": len(rows), "success": sum(r[0] for r in rows), "failed": sum(not r[0] for r in rows), "generator_skipped": skipped, "elapsed_seconds": round(elapsed, 2), "completed_rps": round(len(rows)/elapsed, 2), "p95_ms_including_queue": p95(1), "p95_generator_queue_ms": p95(2), "p95_http_ms": p95(3), "scope": "educational client timings; not a production capacity guarantee"}, indent=2))
