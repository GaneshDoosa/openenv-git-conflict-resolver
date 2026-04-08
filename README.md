---
title: Git Conflict Resolver
emoji: 🔀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags: ["openenv"]
---
# 🔀 Git Conflict Resolver — OpenEnv Environment

An RL environment where AI agents learn to resolve Git merge conflicts.  
Built for the **OpenEnv Hackathon** (Meta × Hugging Face × Scaler).

---

## 🧠 Environment Description & Motivation

Merge conflicts are a daily reality for every software team. Resolving them correctly requires understanding both the syntactic structure of code **and** the semantic intent of diverging branches — a genuinely hard task for AI agents.

This environment presents agents with real Python files containing `<<<<<<< HEAD`, `=======`, and `>>>>>>>` conflict markers. The agent must produce a clean, fully resolved file — no markers, valid syntax, and correct logic.

Unlike toy environments, this simulates:
- **Easy conflicts**: Accept an obvious incoming change (e.g. updated timeout value)
- **Medium conflicts**: Apply different resolution strategies per conflict block
- **Hard conflicts**: Combine additive changes from *both* branches (not just pick one)

---

## 📐 Action & Observation Space

### Observation Space (structured JSON)

| Field | Type | Description |
|-------|------|-------------|
| `task_name` | string | Current task identifier |
| `task_description` | string | Natural language instructions for the agent |
| `filename` | string | Name of the file being resolved |
| `file_language` | string | Language of the file (`python`, `text`) |
| `conflicted_content` | string | Full file content with conflict markers |
| `branch_ours` | string | Name of the HEAD (current) branch |
| `branch_theirs` | string | Name of the incoming branch |
| `num_conflicts` | integer | Number of `<<<<<<<` blocks in the file |
| `last_attempt` | string \| null | Agent's previous resolution (for retry) |
| `last_error` | string \| null | Grading feedback from last step |
| `step` | integer | Current step number |
| `max_steps` | integer | Maximum allowed steps (10) |
| `done` | boolean | Whether the episode is finished |

### Action Space

```json
{
  "resolved_content": "<full resolved file as a string>"
}
```

The agent outputs the **complete file content** with **all conflict markers removed**.

---

## 📋 Task Descriptions

### Task 1: `single_conflict` — Easy
- **File:** `config.py`
- **Conflicts:** 1 block
- **Description:** A timeout value was changed from 30s to 60s on a feature branch. The agent must accept the incoming change.
- **Expected difficulty:** Any capable LLM should solve this in 1–2 steps.

### Task 2: `multi_conflict` — Medium
- **File:** `user_service.py`
- **Conflicts:** 3 blocks
- **Description:** Authentication was refactored. Each block requires a different resolution: accept new import, keep original constant, accept new function implementation.
- **Expected difficulty:** Requires reading context across blocks.

### Task 3: `logic_conflict` — Hard
- **File:** `data_pipeline.py`
- **Conflicts:** 2 blocks
- **Description:** Both branches added valid, additive features. The agent **must combine** them — not simply pick one side. Requires understanding code semantics.
- **Expected difficulty:** Frontier models (GPT-4, Qwen-72B) score ~0.5–0.7 without specific tuning.

---

## 🏆 Reward Function

The reward is **shaped** — agents get feedback at every step, not just at the end.

| Signal | Value | Trigger |
|--------|-------|---------|
| Improvement bonus | `+0.75 × score_delta` | Score improves over previous step |
| Marker-free bonus | `+0.10` | First time no markers remain |
| Perfect match bonus | `+0.25` | Score reaches 1.0 |
| Stagnation penalty | `-0.10` | Identical submission as previous step |
| Step cost | `-0.01 × (step/max_steps)` | Every step |

### Grading Breakdown (per step)

| Component | Score | Criterion |
|-----------|-------|-----------|
| `no_markers` | 0.25 | No `<<<<<<<`, `=======`, `>>>>>>>` in output |
| `valid_syntax` | 0.25 | File parses as valid Python (AST check) |
| `similarity` | 0.25 | Fuzzy match ratio vs. expected resolution |
| `exact_match` | 0.25 | Character-exact match with expected output |

---

## 🚀 Setup & Usage

### Local Setup

```bash
# 1. Install dependencies
pip install -r server/requirements.txt

# 2. Start the server
uvicorn server.main:app --host 0.0.0.0 --port 7860 --app-dir server

# 3. Test the endpoints
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "single_conflict"}'

curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"resolved_content": "# your resolved content here"}'

curl http://localhost:7860/state
```

### Docker

```bash
# Build
docker build -t git-conflict-resolver .

# Run
docker run -p 7860:7860 git-conflict-resolver

# Verify
curl http://localhost:7860/health
```

### Run Baseline Inference

```bash
export HF_TOKEN=your_token_here
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_URL=http://localhost:7860

python inference.py
```

---

## 📊 Baseline Scores

> Scores obtained using `Qwen/Qwen2.5-72B-Instruct` via HF Inference API.

| Task | Score | Steps | Success |
|------|-------|-------|---------|
| `single_conflict` | 1.00 | 1 | ✅ |
| `multi_conflict` | 0.75 | 3 | ❌ |
| `logic_conflict` | 0.50 | 5 | ❌ |
| **Average** | **0.75** | — | — |

---

## 📁 Project Structure

```
openenv_hackathon/
├── server/
│   ├── main.py          # FastAPI server — /reset /step /state /health
│   ├── env.py           # Core environment logic (reset/step/state/close)
│   ├── models.py        # Pydantic Observation, Action, Reward models
│   ├── tasks.py         # Task definitions (3 tasks with conflict content)
│   ├── graders.py       # Deterministic graders (marker, AST, similarity, exact)
│   ├── reward.py        # Shaped reward function
│   └── requirements.txt
├── inference.py         # Baseline inference script (root — required)
├── openenv.yaml         # OpenEnv metadata (required for openenv validate)
├── Dockerfile           # Container build (port 7860 for HF Spaces)
└── README.md
```

---

## 🔧 API Reference

### `POST /reset`
Start a new episode.
```json
{ "task": "single_conflict" }
```
Returns: `ConflictObservation`

### `POST /step`
Submit a conflict resolution.
```json
{ "resolved_content": "# full resolved file..." }
```
Returns: `{ observation, reward, done, info }`

### `GET /state`
Returns current episode state (step, total_reward, history).

### `GET /health`
Returns `{ "status": "ok" }` — used for HF Space validation.

### `GET /tasks`
Returns `{ "tasks": ["single_conflict", "multi_conflict", "logic_conflict"] }`

---

## 👥 Team

**Agent Smith** — OpenEnv Hackathon, April 2026

- Ganesh Doosa (Team Lead)
- Gajula Akanksha
- Yashwanth Kumar
