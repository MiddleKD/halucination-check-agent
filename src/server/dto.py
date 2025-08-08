"""
Data Transfer Objects - 할루시네이션 검사 에이전트의 데이터 구조

이 파일은 에이전트 간 데이터 전달을 위한 모든 데이터 클래스와 모델을 정의합니다.
pydantic과 dataclass를 조합하여 타입 안전성과 직렬화를 보장합니다.
"""

from dataclasses import dataclass, field
from typing import List, Literal

from constant import DEFAULT_FALLBACK_LIMIT, SCORE_DIFF_THRESHOLD
from pydantic import BaseModel, Field
from pydantic_ai.messages import ModelMessage


# ============================================================================
# 🔧 에이전트 의존성 구성
# ============================================================================


@dataclass
class StateDependencies:
    stance_type: Literal["pros", "cons"] = "cons"
    return_reason: bool = False


@dataclass
class CheckSearchGraphState:
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
class CheckSearchGraphOutput:
    score: float
    reason: str | None
    ref_url: List[str]


@dataclass
class CheckContextGraphState:
    return_reason: bool = False
    fall_back_mode: bool = False
    fall_back_limit: int = DEFAULT_FALLBACK_LIMIT
    score_diff_threshold: float = SCORE_DIFF_THRESHOLD
    current_fallback: int = 0

    scores: List[float] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    user_input: str = ""
    user_history: list[ModelMessage] = field(default_factory=list)
    input_context: str = ""


@dataclass
class CheckContextGraphOutput:
    score: float
    reason: str | None


# ============================================================================
# 🤖 에이전트 출력 타입 정의
# ============================================================================

class GetSourceAgentOutputType(BaseModel):
    """검색 에이전트 출력 형식"""
    summary: str = Field(
        description="Summary of the collected reference information"
    )
    ref_url: List[str] = Field(
        description="List of reference URLs that are helpful for verification",
        examples=["https://example.com", "http://context7/pytorch"],
    )


class CtxConsistentAgentOutputType(BaseModel):
    """일관성 평가 에이전트 출력 형식"""
    hallucination_score: float = Field(
        description="Hallucination score (0.0 = consistent, 1.0 = contradictory)",
        ge=0.0,          # 최솟값 0.0
        le=1.0,          # 최댓값 1.0  
        multiple_of=0.1, # 0.1 단위로 반올림
    )
    reason: str = Field(
        description="Detailed explanation for the assigned score"
    )


class ReasonSummaryAgentOutputType(BaseModel):
    """이유 요약 에이전트 출력 형식"""
    summary: str = Field(
        description="Comprehensive summary of evaluation reasons"
    )
