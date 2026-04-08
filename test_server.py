"""Quick smoke test for the Git Conflict Resolver server."""
import urllib.request
import json

BASE = "http://localhost:7860"

def get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.loads(r.read())

def post(path, body=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

print("\n=== /health ===")
h = get("/health")
print(h)
assert h["status"] == "ok", "Health check failed!"

print("\n=== /tasks ===")
t = get("/tasks")
print(t)
assert set(t["tasks"]) == {"single_conflict", "multi_conflict", "logic_conflict"}

print("\n=== /reset (single_conflict) ===")
obs = post("/reset", {"task": "single_conflict"})
print(f"  task_name    : {obs['task_name']}")
print(f"  num_conflicts: {obs['num_conflicts']}")
print(f"  step         : {obs['step']}")
assert obs["num_conflicts"] == 1

print("\n=== /step (correct resolution) ===")
correct = """\
# config.py
# Application configuration

APP_NAME = "MyService"
APP_VERSION = "2.1.0"
DEBUG = False

# Network settings
HOST = "0.0.0.0"
PORT = 8080

REQUEST_TIMEOUT = 60  # seconds \u2014 updated for slow upstream APIs

MAX_RETRIES = 3
LOG_LEVEL = "INFO"
"""
resp = post("/step", {"resolved_content": correct})
print(f"  score         : {resp['info']['score']}")
print(f"  reward        : {resp['reward']['value']}")
print(f"  done          : {resp['done']}")
print(f"  partial_scores: {resp['reward']['partial_scores']}")
assert resp["info"]["score"] == 1.0, f"Expected score 1.0, got {resp['info']['score']}"
assert resp["done"] is True

print("\n=== /step (wrong — markers still present) ===")
post("/reset", {"task": "single_conflict"})
bad = "<<<<<<< HEAD\nREQUEST_TIMEOUT = 30\n=======\nREQUEST_TIMEOUT = 60\n>>>>>>> feature"
resp2 = post("/step", {"resolved_content": bad})
print(f"  score : {resp2['info']['score']}  (expected 0.0)")
assert resp2["info"]["score"] == 0.0

print("\n=== /state ===")
s = get("/state")
print(f"  step: {s['step']}  total_reward: {s['total_reward']}")

print("\n" + "="*40)
print("  ALL TESTS PASSED ✅")
print("="*40 + "\n")
