from pydantic_ai import Agent

from constant import REASON_SUMMARY_AGENT_MODEL
from dto import ReasonSummaryAgentOutputType, StateDependencies

reason_summary_agent = Agent(
    REASON_SUMMARY_AGENT_MODEL,
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
    instrument=True,
)
