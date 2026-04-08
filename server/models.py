from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class ConflictObservation(BaseModel):
    """What the agent sees at each step."""
    task_name: str = Field(description="Name of the current task")
    task_description: str = Field(description="What the agent must do")
    filename: str = Field(description="Name of the file being resolved")
    file_language: str = Field(description="Programming language of the file (python, text, etc.)")
    conflicted_content: str = Field(description="Full file content with Git conflict markers")
    branch_ours: str = Field(description="Name of the HEAD (ours) branch")
    branch_theirs: str = Field(description="Name of the incoming (theirs) branch")
    num_conflicts: int = Field(description="Number of conflict blocks in the file")
    last_attempt: Optional[str] = Field(default=None, description="Agent's previous resolution attempt")
    last_error: Optional[str] = Field(default=None, description="Feedback from last grading")
    step: int = Field(default=0)
    max_steps: int = Field(default=10)
    done: bool = Field(default=False)


class ConflictAction(BaseModel):
    """The action the agent takes — the resolved file content."""
    resolved_content: str = Field(
        description="The full file content after resolving all conflict markers. "
                    "Must contain NO <<<<<<<, =======, or >>>>>>> lines."
    )


class ConflictReward(BaseModel):
    """Reward signal returned after each step."""
    value: float = Field(ge=0.0, le=1.0, description="Reward value between 0.0 and 1.0")
    reason: str = Field(description="Human-readable explanation of the reward")
    partial_scores: Dict[str, float] = Field(default_factory=dict)


class StepResponse(BaseModel):
    """Full response from a step."""
    observation: ConflictObservation
    reward: ConflictReward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetRequest(BaseModel):
    """Request body for /reset."""
    task: str = Field(
        default="single_conflict",
        description="Task name: single_conflict | multi_conflict | logic_conflict"
    )


class StateResponse(BaseModel):
    """Current internal state of the environment."""
    task_name: Optional[str]
    step: int
    done: bool
    total_reward: float
    history: List[Dict[str, Any]]
