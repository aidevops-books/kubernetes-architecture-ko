from pathlib import Path
from common import kubectl, require_lab

require_lab()
target = Path(__file__).resolve().parent.parent / "backups/cloudshop.dump"
if target.exists():
    raise SystemExit("Backup already exists. Archive it under another name before making a new backup.")
data = kubectl("exec", "-n", "cloudshop", "postgres-0", "--", "pg_dump", "-U", "cloudshop", "-d", "cloudshop", "-Fc")
if not data.startswith(b"PGDMP"):
    raise SystemExit("Unexpected backup format")
target.parent.mkdir(exist_ok=True)
target.write_bytes(data)
print(f"Saved {len(data)} bytes to {target}")
