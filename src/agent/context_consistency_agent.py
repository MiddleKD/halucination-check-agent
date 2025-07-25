from pydantic_ai import Agent, RunContext

from constant import CONTEXT_CONSISTENCY_AGENT_MODEL
from dto import CtxConsistentAgentOutputType
from dto import StateDependencies

context_consistency_agent = Agent(
    CONTEXT_CONSISTENCY_AGENT_MODEL,
    deps_type=StateDependencies,
    output_type=CtxConsistentAgentOutputType,
    instrument=True,
)


@context_consistency_agent.instructions
async def set_instructions(ctx: RunContext[StateDependencies]) -> str:
    attach_prompt = ""

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
