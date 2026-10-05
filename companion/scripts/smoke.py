import argparse
import json
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request(base, path, data=None, key=None):
    headers = {"Content-Type": "application/json", "X-Request-ID": "smoke-"+str(uuid.uuid4())}
    if key:
        headers["Idempotency-Key"] = key
    req = Request(base+path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    try:
        with urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


def run(base):
    status, products = request(base, "/api/products")
    assert status == 200 and len(products["products"]) == 3, (status, products)
    key = "smoke-"+str(uuid.uuid4())
    data = {"product_id": 1, "quantity": 2}
    status, created = request(base, "/api/orders", data, key)
    assert status == 201, (status, created)
    order_id = created["order"]["id"]
    status, repeated = request(base, "/api/orders", data, key)
    assert status == 200 and repeated["order"]["id"] == order_id
    assert request(base, "/api/orders", {"product_id": 1, "quantity": 3}, key)[0] == 409
    assert request(base, "/api/orders/"+order_id)[1]["order"]["quantity"] == 2
    assert request(base, "/api/orders", {"product_id": 1, "quantity": -1}, str(uuid.uuid4()))[0] == 400
    assert request(base, "/api/orders", {"product_id": 1, "quantity": 1})[0] == 400
    print("PASS: products, create, repeat, conflict, read, invalid quantity, missing key")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080")
    run(parser.parse_args().base)
