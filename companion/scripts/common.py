import json
import subprocess


def kubectl(*args, input=None):
    return subprocess.run(["kubectl", *args], input=input, capture_output=True, check=True).stdout


def require_lab():
    ns = json.loads(kubectl("get", "namespace", "cloudshop", "-o", "json"))
    if ns.get("metadata", {}).get("labels", {}).get("purpose") != "architecture-book-lab":
        raise SystemExit("Refusing: cloudshop namespace lacks the book lab label")


def psql(sql, database="cloudshop"):
    return kubectl("exec", "-n", "cloudshop", "postgres-0", "--", "psql", "-U", "cloudshop", "-d", database, "-v", "ON_ERROR_STOP=1", "-At", "-c", sql)
