"""
FastAPI server for the Git Conflict Resolver OpenEnv environment.

Endpoints:
  POST /reset  — start a new episode
  POST /step   — submit a resolution attempt
  GET  /state  — get current episode state
  GET  /health — liveness check (HF Space ping)
  GET  /tasks  — list available tasks
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from env import GitConflictEnv
from models import (
    ConflictAction,
    ConflictObservation,
    ResetRequest,
    StateResponse,
    StepResponse,
)
from tasks import list_tasks

app = FastAPI(
    title="Git Conflict Resolver — OpenEnv",
    description=(
        "An RL environment where agents learn to resolve Git merge conflicts. "
        "Implements the OpenEnv spec: reset(), step(), state()."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single shared environment instance (stateful per session)
env = GitConflictEnv()


@app.get("/health")
def health():
    """Liveness check — must return 200 for HF Space validation."""
    return {"status": "ok", "env": "git-conflict-resolver"}


@app.get("/tasks")
def get_tasks():
    """List all available tasks."""
    return {"tasks": list_tasks()}


@app.post("/reset", response_model=ConflictObservation)
def reset(request: ResetRequest = None):
    """
    Reset the environment and start a new episode.

    Body (optional):
        { "task": "single_conflict" }   # or multi_conflict | logic_conflict
    """
    task_name = (request.task if request else None) or "single_conflict"
    try:
        obs = env.reset(task_name=task_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return obs


@app.post("/step", response_model=StepResponse)
def step(action: ConflictAction):
    """
    Submit a resolved file content as the agent's action.

    Body:
        { "resolved_content": "# full file content here..." }
    """
    try:
        response = env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return response


@app.get("/state", response_model=StateResponse)
def state():
    """Return the current internal state of the environment."""
    return env.state()

def main(host: str = "0.0.0.0", port: int | None = None):
    import uvicorn
    import os
    if port is None:
        port = int(os.getenv("API_PORT", "7860"))
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()

