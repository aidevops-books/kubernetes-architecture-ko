from pathlib import Path
from common import kubectl, require_lab, psql

require_lab()
data = (Path(__file__).resolve().parent.parent / "backups/cloudshop.dump").read_bytes()
if psql("SELECT 1 FROM pg_database WHERE datname='restorecheck'", "postgres").strip():
    raise SystemExit("restorecheck already exists; no overwrite performed")
psql("CREATE DATABASE restorecheck", "postgres")
kubectl("exec", "-i", "-n", "cloudshop", "postgres-0", "--", "pg_restore", "--exit-on-error", "-U", "cloudshop", "-d", "restorecheck", input=data)
print("Restored rows:", psql("SELECT count(*) FROM orders", "restorecheck").decode().strip())
print("Check expected order IDs separately. Original cloudshop database was not replaced.")
