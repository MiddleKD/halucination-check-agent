"""
Context Consistency Agent - NLI 기반 할루시네이션 검출 에이전트

주어진 문맥(context)과 검증할 문장(sentence) 사이의 일관성을 평가하여
할루시네이션 가능성을  0.0-1.0 점수로 반환합니다.

핵심 개념:
- 0.0: 문맥과 완전히 일치 (할루시네이션 없음)
- 1.0: 문맥과 완전히 모순 (할루시네이션 확실)
"""

from constant import CONTEXT_CONSISTENCY_AGENT_MODEL
from dto import CtxConsistentAgentOutputType, StateDependencies
from pydantic_ai import Agent, RunContext

# NLI 기반 할루시네이션 평가 에이전트 초기화
# GPT-4o 모델을 사용하여 높은 정확도의 일관성 평가를 수행
context_consistency_agent = Agent(
    CONTEXT_CONSISTENCY_AGENT_MODEL,  # "openai:gpt-4o"
    deps_type=StateDependencies,
    output_type=CtxConsistentAgentOutputType,
    instrument=True,  # Langfuse 추적 활성화
)


@context_consistency_agent.instructions
async def set_instructions(ctx: RunContext[StateDependencies]) -> str:
    """
    동적으로 프롬프트 생성 - 이유 설명 포함 여부를 런타임에 결정
    
    Args:
        ctx: 실행 컨텍스트 (return_reason 플래그 포함)
    
    Returns:
        str: 에이전트에게 전달할 지시사항
    """
    attach_prompt = ""

    # 이유 설명 요청 여부에 따라 프롬프트 조정
    match ctx.deps.return_reason:
        case True:
            attach_prompt = (
                "- reason: explanation for the score, based only on the context."
            )
        case False:
            pass

    return (
        "You are an expert factual consistency evaluator. "
        "Your task is to assess whether a given sentence is supported by a provided context.\n\n"
        "You must return below items: \n"
        "- hallucination_score: float between 0.0 (fully supported) and 1.0 (entirely hallucinated).\n"
        f"{attach_prompt}"
    )
