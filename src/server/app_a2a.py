from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentProvider, AgentSkill
from graph import convert_graph_as_agent

agent_executor = convert_graph_as_agent()


def main(host, port):
    capabilities = AgentCapabilities(streaming=False, push_notifications=False)
    skill = AgentSkill(
        id="hallucination_check_agent",
        name="Halucination Check Agent",
        description="Halucination Check Agent",
        tags=["halucination", "check"],
        examples=["Check if the text is a hallucination"],
        input_modes=["application/json"],
        output_modes=["application/json"],
    )

    agent_card = AgentCard(
        name="hallucination_check_agent",
        description="Halucination Check Agent",
        url="http://localhost:8008",
        version="0.0.1",
        provider=AgentProvider(
            organization="seocho-data-study", url="https://github.com/cdkkim/data-study"
        ),
        capabilities=capabilities,
        skills=[skill],
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    return server.build()


app = main("localhost", 8008)
