import argparse
import json
from common import kubectl, require_lab

parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["readiness-break", "readiness-restore"])
args = parser.parse_args()
require_lab()
path = "/missing-readiness" if args.action == "readiness-break" else "/readyz"
patch = {"spec": {"template": {"spec": {"containers": [{"name": "api", "readinessProbe": {"httpGet": {"path": path, "port": 8080}}}]}}}}
kubectl("patch", "deployment", "api", "-n", "cloudshop", "--type=strategic", "-p", json.dumps(patch))
print("Applied", args.action, "- inspect new and old Pods separately.")
