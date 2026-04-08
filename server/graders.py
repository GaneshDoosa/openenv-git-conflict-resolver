"""
Deterministic graders for the Git Conflict Resolver environment.

Scoring breakdown per step:
  - no_markers:    0.25 — no conflict markers remain in the output
  - valid_syntax:  0.25 — file parses as valid Python (if python file)
  - similarity:    0.25 — fuzzy similarity to expected resolution
  - exact_match:   0.25 — character-exact match with expected output
"""

import ast
import difflib
import re
from typing import Any, Dict, Tuple

CONFLICT_MARKERS = ["<<<<<<<", "=======", ">>>>>>>"]


def has_conflict_markers(content: str) -> bool:
    return any(marker in content for marker in CONFLICT_MARKERS)


def count_conflict_blocks(content: str) -> int:
    return len(re.findall(r"^<<<<<<<", content, re.MULTILINE))


def is_valid_python(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def similarity_ratio(a: str, b: str) -> float:
    """SequenceMatcher similarity between two strings (0.0 to 1.0)."""
    return difflib.SequenceMatcher(None, a.strip(), b.strip()).ratio()


def grade(
    task: Dict[str, Any],
    resolved_content: str,
) -> Tuple[float, str, Dict[str, float]]:
    """
    Grade the agent's resolved file content.

    Returns (total_score, reason_string, partial_scores_dict)
    """
    expected = task["expected_resolved"]
    language = task.get("file_language", "text")

    partial: Dict[str, float] = {
        "no_markers": 0.0,
        "valid_syntax": 0.0,
        "similarity": 0.0,
        "exact_match": 0.0,
    }
    reasons = []

    # 1. No conflict markers remaining
    if not has_conflict_markers(resolved_content):
        partial["no_markers"] = 0.25
        reasons.append("No conflict markers remain (+0.25)")
    else:
        remaining = count_conflict_blocks(resolved_content)
        reasons.append(f"{remaining} conflict block(s) still unresolved (+0.0)")
        # If markers remain, we still check the rest for partial credit
        # but file is definitely not done
        total = sum(partial.values())
        clamped_score = round(0.01 + (total * 0.98), 3)
        return clamped_score, " | ".join(reasons), partial

    # 2. Valid syntax (for Python files)
    if language == "python":
        if is_valid_python(resolved_content):
            partial["valid_syntax"] = 0.25
            reasons.append("Valid Python syntax (+0.25)")
        else:
            reasons.append("Invalid Python syntax (+0.0)")
    else:
        # For non-Python files, give full credit if no markers
        partial["valid_syntax"] = 0.25
        reasons.append("Non-Python file, syntax check skipped (+0.25)")

    # 3. Similarity score
    sim = similarity_ratio(resolved_content, expected)
    sim_score = round(sim * 0.25, 3)
    partial["similarity"] = sim_score
    reasons.append(f"Similarity to expected: {sim:.2%} → +{sim_score:.3f}")

    # 4. Exact match
    if resolved_content.strip() == expected.strip():
        partial["exact_match"] = 0.25
        reasons.append("Exact match with expected resolution (+0.25)")
    else:
        reasons.append("Does not exactly match expected resolution (+0.0)")

    total = min(1.0, sum(partial.values()))
    # Map [0, 1] -> [0.01, 0.99] to satisfy "strictly between 0 and 1" requirement
    clamped_score = round(0.01 + (total * 0.98), 3)
    return clamped_score, " | ".join(reasons), partial
