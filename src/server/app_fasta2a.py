# for very simple demo

from fasta2a.schema import AgentProvider, Skill
from check_search_graph import convert_graph_as_agent

agent = convert_graph_as_agent()

provider = AgentProvider(
    organization="seocho-data-study", url="https://github.com/cdkkim/data-study"
)
agent_skill = Skill(
    id="hallucination_check_agent",
    name="Halucination Check Agent",
    description="Halucination Check Agent",
    tags=["halucination", "check"],
    examples=["Check if the text is a hallucination"],
    input_modes=["application/json"],
    output_modes=["application/json"],
)

app = agent.to_a2a(
    name="hallucination_check_agent",
    url="http://localhost:8008",
    version="0.0.1",
    description="Halucination Check Agent",
    provider=provider,
    skills=[agent_skill],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)
