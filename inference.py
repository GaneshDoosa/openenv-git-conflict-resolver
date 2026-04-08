"""
inference.py — Baseline inference script for Git Conflict Resolver OpenEnv
================================================================================
MANDATORY environment variables:
  API_BASE_URL   — LLM API endpoint  (default: HF Inference API)
  MODEL_NAME     — Model identifier  (default: Qwen/Qwen2.5-72B-Instruct)
  HF_TOKEN       — Hugging Face / API key (REQUIRED, no default)
  ENV_URL        — URL of the running OpenEnv server
                   (default: http://localhost:7860)

STDOUT FORMAT (strict — do not modify):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
================================================================================
"""

import os
import json
import sys
import textwrap
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Environment variables ────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")
ENV_URL      = os.getenv("ENV_URL", "https://doosaganesh-openenv-git-conflict-resolver.hf.space")
BENCHMARK    = "git-conflict-resolver"
MAX_STEPS    = 10

if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

# ── HTTP helpers (no extra deps — stdlib only) ────────────────────────────────

def _http(method: str, path: str, body: Optional[Dict] = None) -> Dict:
    url = f"{ENV_URL}{path}"
    data = json.dumps(body).encode() if body is not None else b"{}"
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def env_reset(task: str) -> Dict:
    return _http("POST", "/reset", {"task": task})


def env_step(resolved_content: str) -> Dict:
    return _http("POST", "/step", {"resolved_content": resolved_content})


def env_state() -> Dict:
    return _http("GET", "/state")


# ── Agent prompt builder ──────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert software engineer specializing in Git merge conflict resolution.

    You will be given a file containing Git conflict markers:
      <<<<<<< HEAD       — start of current branch (ours)
      =======            — separator
      >>>>>>> <branch>   — end of incoming branch (theirs)

    Your task:
    1. Carefully read the conflicted file and the task description.
    2. Resolve ALL conflict blocks according to the instructions.
    3. Return ONLY the complete resolved file content — no explanations, no markdown fences, no extra text.
    4. The output must contain ZERO conflict markers.
""")


def build_user_prompt(obs: Dict) -> str:
    lines = [
        f"Task: {obs['task_description']}",
        f"File: {obs['filename']} (language: {obs['file_language']})",
        f"Branch ours: {obs['branch_ours']}  |  Branch theirs: {obs['branch_theirs']}",
        f"Conflict blocks remaining: {obs['num_conflicts']}",
        "",
        "=== CONFLICTED FILE ===",
        obs["conflicted_content"],
        "=== END OF FILE ===",
    ]
    if obs.get("last_error"):
        lines += ["", f"Feedback from last attempt: {obs['last_error']}"]
    if obs.get("last_attempt"):
        lines += ["", "Your previous attempt (failed):", obs["last_attempt"]]
    lines += ["", "Output ONLY the fully resolved file content:"]
    return "\n".join(lines)


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_task(task_name: str) -> Dict[str, Any]:
    obs = env_reset(task_name)
    model_short = MODEL_NAME.split("/")[-1]

    print(f"[START] task={task_name} env={BENCHMARK} model={model_short}", flush=True)

    rewards: List[float] = []
    final_score = 0.0
    success = False

    for step_num in range(1, MAX_STEPS + 1):
        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": build_user_prompt(obs)},
        ]

        # Call LLM
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            resolved = response.choices[0].message.content.strip()
        except Exception as e:
            resolved = obs.get("conflicted_content", "")
            error_msg = str(e)
        else:
            error_msg = None

        # Submit action to env
        try:
            step_resp = env_step(resolved)
        except Exception as e:
            print(
                f"[STEP] step={step_num} action=<env_error> reward=0.00 "
                f"done=false error={str(e)[:80]}",
                flush=True,
            )
            break

        reward_val = step_resp["reward"]["value"]
        done       = step_resp["done"]
        info       = step_resp.get("info", {})
        final_score = info.get("score", 0.0)
        obs        = step_resp["observation"]

        # Truncate action for log line (keep it single-line)
        action_preview = resolved[:60].replace("\n", "\\n")
        error_log = error_msg[:80] if error_msg else "null"

        print(
            f"[STEP] step={step_num} "
            f"action=\"{action_preview}...\" "
            f"reward={reward_val:.2f} "
            f"done={'true' if done else 'false'} "
            f"error={error_log}",
            flush=True,
        )

        rewards.append(reward_val)

        if done:
            success = final_score >= 1.0
            break

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={'true' if success else 'false'} "
        f"steps={len(rewards)} "
        f"score={final_score:.2f} "
        f"rewards={rewards_str}",
        flush=True,
    )

    return {"task": task_name, "score": final_score, "success": success, "steps": len(rewards)}


# ── Main entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    tasks = ["single_conflict", "multi_conflict", "logic_conflict"]
    results = []
    for task in tasks:
        result = run_task(task)
        results.append(result)

    # Summary
    print("\n=== BASELINE SUMMARY ===", flush=True)
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"  {status}  {r['task']:<20} score={r['score']:.2f}  steps={r['steps']}", flush=True)

    avg = sum(r["score"] for r in results) / len(results)
    print(f"\n  Average score: {avg:.2f}", flush=True)
