
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentProvider, AgentSkill, AgentExtension
from executor import HallucinationCheckExecutor
from constant import A2A_SEARCH_ENGINE_EXTENSION_URI, A2A_SET_INPUT_CONTEXT_EXTENSION_URI

def main(host, port):
    extensions = [
        AgentExtension(
            uri=A2A_SEARCH_ENGINE_EXTENSION_URI,
            description="Use tavily search engine if context is not provided",
            required=False,
            params={
                "enable": {
                    "type": "bool",
                    "description": "Enable tavily search engine, if true then do not use `set_input_context_explicitly` extension.",
                    "examples": True
                }
            }
        ),
        AgentExtension(
            uri=A2A_SET_INPUT_CONTEXT_EXTENSION_URI,
            description="Set context explicitly based on user input",
            required=False,
            params={
                "input_context": {
                    "type": "string",
                    "description": "The context to be set explicitly",
                    "examples": "RESUME: My name is John. I am 30 years old.\n Company Profile: Startup in Seoul, founded in 2020, with 10 employees.",
                }
            },
        ),
    ]

    capabilities = AgentCapabilities(streaming=True, push_notifications=False, extensions=extensions)

    skill = AgentSkill(
        id="hallucination_check_agent",
        name="Halucination Check Agent",
        description="Halucination Check Agent",
        tags=["halucination", "check"],
        examples=["ONNX is faster than TensorRT."],
        input_modes=["application/json"],
        output_modes=["application/json"],
    )

    agent_card = AgentCard(
        name="hallucination_check_agent",
        description="Halucination Check Agent",
        url=f"http://{host}:{port}",
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
        agent_executor=HallucinationCheckExecutor(),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main("localhost", 8008)
