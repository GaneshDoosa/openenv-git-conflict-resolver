"""
Core OpenEnv environment: Git Conflict Resolver.

OpenEnv interface:
  - reset(task_name) → ConflictObservation
  - step(action)     → StepResponse
  - state()          → StateResponse
"""

from typing import Any, Dict, List, Optional

from graders import grade
from models import (
    ConflictAction,
    ConflictObservation,
    ConflictReward,
    StateResponse,
    StepResponse,
)
from reward import compute_reward
from tasks import get_task

MAX_STEPS = 10


class GitConflictEnv:
    def __init__(self):
        self._task: Optional[Dict[str, Any]] = None
        self._step: int = 0
        self._done: bool = False
        self._total_reward: float = 0.0
        self._history: List[Dict[str, Any]] = []
        self._last_attempt: Optional[str] = None
        self._last_score: float = 0.0

    # ──────────────────────────────────────────────
    # OpenEnv Interface
    # ──────────────────────────────────────────────

    def reset(self, task_name: str = "single_conflict") -> ConflictObservation:
        """Reset the environment for a new episode."""
        self._task = get_task(task_name)
        self._step = 0
        self._done = False
        self._total_reward = 0.0
        self._history = []
        self._last_attempt = None
        self._last_score = 0.0

        return self._build_obs(last_error=None)

    def step(self, action: ConflictAction) -> StepResponse:
        """Execute one step: grade the agent's resolved file and return feedback."""
        if self._task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._step += 1
        resolved = action.resolved_content

        # Grade
        score, grade_reason, partial_scores = grade(self._task, resolved)

        # Shaped reward
        reward_val, reward_reason = compute_reward(
            current_score=score,
            previous_score=self._last_score,
            resolved_content=resolved,
            previous_attempt=self._last_attempt,
            step=self._step,
            max_steps=MAX_STEPS,
            partial_scores=partial_scores,
        )

        # Update state
        self._last_attempt = resolved
        self._last_score = score
        self._total_reward += reward_val

        done = score >= 0.98 or self._step >= MAX_STEPS
        self._done = done

        # Build feedback for next observation
        last_error = None if score >= 0.98 else grade_reason

        obs = self._build_obs(last_error=last_error)
        obs.last_attempt = resolved
        obs.step = self._step
        obs.done = done

        reward = ConflictReward(
            value=reward_val,
            reason=f"[Grade] {grade_reason} || [Reward] {reward_reason}",
            partial_scores=partial_scores,
        )

        self._history.append({
            "step": self._step,
            "score": score,
            "reward": reward_val,
            "partial_scores": partial_scores,
        })

        return StepResponse(
            observation=obs,
            reward=reward,
            done=done,
            info={
                "score": score,
                "total_reward": round(self._total_reward, 3),
                "grade_reason": grade_reason,
            },
        )

    def state(self) -> StateResponse:
        """Return the current internal environment state."""
        return StateResponse(
            task_name=self._task["name"] if self._task else None,
            step=self._step,
            done=self._done,
            total_reward=round(self._total_reward, 3),
            history=self._history,
        )

    def close(self):
        pass

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _build_obs(self, last_error: Optional[str]) -> ConflictObservation:
        t = self._task
        return ConflictObservation(
            task_name=t["name"],
            task_description=t["description"],
            filename=t["filename"],
            file_language=t["file_language"],
            conflicted_content=t["conflicted_content"],
            branch_ours=t["branch_ours"],
            branch_theirs=t["branch_theirs"],
            num_conflicts=t["num_conflicts"],
            last_attempt=self._last_attempt,
            last_error=last_error,
            step=self._step,
            max_steps=MAX_STEPS,
            done=self._done,
        )
