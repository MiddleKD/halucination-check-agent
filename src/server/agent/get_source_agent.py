"""
Get Source Agent - 검색 기반 컨텍스트 수집 에이전트

Tavily 검색 엔진을 사용하여 주어진 질의에 대한 관련 정보를 수집하고
할루시네이션 검증을 위한 컨텍스트를 구성합니다.

주요 기능:
- Tavily 검색을 통한 실시간 정보 수집
- Pro/Con 관점에 따른 편향 검색 지원
- 참조 URL과 요약 정보 제공
"""

import os

from constant import GET_SOURCE_AGENT_MODEL
from dto import GetSourceAgentOutputType, StateDependencies
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool

# 컨텍스트 수집 에이전트 초기화
# GPT-3.5-turbo를 사용하여 효율적인 검색 및 요약 수행
get_source_agent = Agent(
    GET_SOURCE_AGENT_MODEL,  # "openai:gpt-3.5-turbo"
    deps_type=StateDependencies,
    output_type=GetSourceAgentOutputType,
    tools=[tavily_search_tool(os.getenv("TAVILY_API_KEY"))],  # Tavily 검색 도구
    instrument=True,  # Langfuse 추적 활성화
)


@get_source_agent.instructions
async def set_instructions(ctx: RunContext[StateDependencies]) -> str:
    """
    검색 관점에 따른 동적 프롬프트 생성
    
    Args:
        ctx: 실행 컨텍스트 (stance_type: pros/cons 포함)
    
    Returns:
        str: 검색 전략이 반영된 지시사항
    """
    attach_prompt = ""

    # 검색 관점 설정: 찬성/반대 관점에 따른 편향 검색
    match ctx.deps.stance_type:
        case "pros":
            attach_prompt = "Assume the query is true, "
        case "cons":
            attach_prompt = "Assume the query is false, "

    return (
        "You are an expert in fact-checking technical information.\n"
        "Your mission is to explore sources to fact-check the given query.\n"
        f"**{attach_prompt}**search for supporting evidence using the given tools.\n"
        "Organize and return the collected information.\n"
        "**Personal opinions are not allowed in response — respond only with factual content.**\n"
    )
