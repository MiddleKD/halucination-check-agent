import os

from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool

from constant import GET_SOURCE_AGENT_MODEL
from dto import GetSourceAgentOutputType, StateDependencies

get_source_agent = Agent(
    GET_SOURCE_AGENT_MODEL,
    deps_type=StateDependencies,
    output_type=GetSourceAgentOutputType,
    tools=[tavily_search_tool(os.getenv("TAVILY_API_KEY"))],
    instrument=True,
)


@get_source_agent.instructions
async def set_instructions(ctx: RunContext[StateDependencies]) -> str:
    attach_prompt = ""

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
