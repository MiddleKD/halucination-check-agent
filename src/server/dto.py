from dataclasses import dataclass, field
from typing import List, Literal

from pydantic import BaseModel, Field
from pydantic_ai.messages import ModelMessage

from constant import DEFAULT_FALLBACK_LIMIT, SCORE_DIFF_THRESHOLD


@dataclass
class StateDependencies:
    stance_type: Literal["pros", "cons"] = "cons"
    return_reason: bool = False


@dataclass
class GraphState:
    stance_type: Literal["pros", "cons", "both"] = "cons"
    fall_back_mode: bool = False
    return_reason: bool = False
    fall_back_limit: int = DEFAULT_FALLBACK_LIMIT
    score_diff_threshold: float = SCORE_DIFF_THRESHOLD
    current_fallback: int = 0

    scores: List[float] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    ref_url: List[str] = field(default_factory=list)

    user_input: str = ""
    user_history: list[ModelMessage] = field(default_factory=list)


@dataclass
class GraphOutput:
    score: float
    reason: str | None
    ref_url: List[str]


class GetSourceAgentOutputType(BaseModel):
    summary: str = Field(description="Summary of the reference")
    ref_url: List[str] = Field(
        description="List of reference URL which is helpful to answer",
        examples=["https://example.com", "http://context7/pytorch"],
    )


class CtxConsistentAgentOutputType(BaseModel):
    hallucination_score: float = Field(
        description="Score of hallucination (1.0 = contradictory / 0.0 = consistent)",
        ge=0.0,
        le=1.0,
        multiple_of=0.1,
    )
    reason: str = Field(description="Reason of the score")


class ReasonSummaryAgentOutputType(BaseModel):
    summary: str = Field(description="Summary of the reason")
