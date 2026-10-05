"""Create a random lab credential once; never silently rotate an existing DB password."""
import json
import secrets
from pathlib import Path
from common import kubectl, require_lab

root = Path(__file__).resolve().parent.parent
kubectl("apply", "-f", str(root / "k8s/00-namespace.yaml"))
require_lab()
existing = kubectl("get", "secret", "db-credentials", "-n", "cloudshop", "--ignore-not-found", "-o", "json")
if existing.strip():
    print("Existing db-credentials retained; no password rotation performed.")
else:
    doc = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "db-credentials", "namespace": "cloudshop"}, "type": "Opaque", "stringData": {"DB_PASSWORD": secrets.token_urlsafe(24)}}
    kubectl("create", "-f", "-", input=json.dumps(doc).encode())
    print("Created lab secret; value is not printed or stored in source files.")
