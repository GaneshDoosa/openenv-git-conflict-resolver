"""
Shaped reward function for the Git Conflict Resolver environment.
Provides dense feedback throughout the episode.
"""

from typing import Dict, Optional, Tuple


def compute_reward(
    current_score: float,
    previous_score: float,
    resolved_content: str,
    previous_attempt: Optional[str],
    step: int,
    max_steps: int,
    partial_scores: Dict[str, float],
) -> Tuple[float, str]:
    """
    Compute a shaped reward for a single step.

    Components:
      + improvement bonus: proportional to score improvement
      + marker-free bonus: first time markers are fully removed
      + perfect bonus: agent hits score >= 1.0
      - stagnation penalty: identical submission as previous step
      - step cost: tiny per-step pressure to be efficient

    Returns (reward_value in [0.0, 1.0], reason_string)
    """
    reasons = []
    reward = 0.0

    # --- Improvement bonus ---
    improvement = current_score - previous_score
    if improvement > 0:
        bonus = round(improvement * 0.75, 3)
        reward += bonus
        reasons.append(f"Score improved +{improvement:.2f} → +{bonus:.3f}")
    elif improvement < 0:
        reasons.append("Score regressed (no bonus)")

    # --- Marker-free bonus (first time no markers remain) ---
    if partial_scores.get("no_markers", 0) > 0 and previous_score == 0.0:
        reward += 0.1
        reasons.append("First clean (no markers) → +0.10")

    # --- Perfect score bonus ---
    if current_score >= 0.98:
        reward += 0.25
        reasons.append("Near-perfect resolution bonus → +0.25")

    # --- Stagnation penalty ---
    if (
        previous_attempt is not None
        and resolved_content.strip() == previous_attempt.strip()
    ):
        reward -= 0.1
        reasons.append("Identical to previous attempt → -0.10")

    # --- Step cost ---
    step_cost = round(0.01 * (step / max_steps), 3)
    reward -= step_cost
    reasons.append(f"Step cost → -{step_cost:.3f}")

    # Map [0, 1] -> [0.01, 0.99]
    reward = round(0.01 + (max(0.0, min(1.0, reward)) * 0.98), 3)
    return reward, " | ".join(reasons)
