"""
Reason Summary Agent - 할루시네이션 평가 결과 요약 에이전트

여러 번의 할루시네이션 평가에서 나온 이유들을 종합하여
사용자가 이해하기 쉬운 한국어 요약문으로 정리합니다.

주요 기능:
- 다중 평가 결과의 이유 통합
- 300자 이내 한국어 요약 생성
- 핵심 인사이트 추출
"""

from constant import REASON_SUMMARY_AGENT_MODEL
from dto import ReasonSummaryAgentOutputType, StateDependencies
from pydantic_ai import Agent

# 이유 요약 에이전트 초기화
# GPT-4o를 사용하여 고품질 한국어 요약 생성
reason_summary_agent = Agent(
    REASON_SUMMARY_AGENT_MODEL,  # "openai:gpt-4o"
    deps_type=StateDependencies,
    output_type=ReasonSummaryAgentOutputType,
    instructions=(
        "You are an expert in identifying and summarizing the reasons "
        "behind hallucination scores in factual consistency evaluations.\n"
        "Given a list of `reason` strings that explain "
        "why a hallucination score was assigned to specific sentences, "
        "your task is to extract the most important insights and summarize them clearly and concisely.\n"
        "**Your reason summary must be a clean, fluent summary within 300 characters.**"
        "RESPONSE IN KOREAN"
    ),
    instrument=True,  # Langfuse 추적 활성화
)
