
"""
A2A Protocol Server - Agent-to-Agent 프로토콜 서버 애플리케이션

할루시네이션 검사 에이전트를 A2A 프로토콜로 제공하는 메인 서버입니다.
두 가지 확장을 지원하여 다양한 컨텍스트 제공 방식을 처리합니다.

주요 기능:
- A2A 프로토콜 준수 서버
- Tavily 검색 엔진 확장 지원
- 명시적 컨텍스트 설정 확장 지원
- 스트리밍 응답 지원
"""

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, 
    AgentCard, 
    AgentProvider, 
    AgentSkill, 
    AgentExtension
)
from executor import HallucinationCheckExecutor
from constant import (
    A2A_SEARCH_ENGINE_EXTENSION_URI, 
    A2A_SET_INPUT_CONTEXT_EXTENSION_URI
)

def main(host: str, port: int) -> None:
    """
    A2A 프로토콜 서버 메인 함수
    
    Args:
        host: 서버 호스트 주소
        port: 서버 포트 번호
    """
    # A2A 확장 정의 - 두 가지 컨텍스트 제공 방식
    extensions = [
        # 확장 1: Tavily 검색 엔진을 통한 자동 컨텍스트 수집
        AgentExtension(
            uri=A2A_SEARCH_ENGINE_EXTENSION_URI,
            description="Use Tavily search engine to automatically collect context information",
            required=False,  # 선택적 확장
            params={
                "enable": {
                    "type": "bool",
                    "description": "Enable Tavily search engine for context collection. Cannot be used with explicit context extension.",
                    "examples": True
                }
            }
        ),
        # 확장 2: 사용자가 명시적으로 제공하는 컨텍스트 사용
        AgentExtension(
            uri=A2A_SET_INPUT_CONTEXT_EXTENSION_URI,
            description="Use explicitly provided context for hallucination evaluation",
            required=False,  # 선택적 확장
            params={
                "input_context": {
                    "type": "string",
                    "description": "Context information to be used for consistency evaluation",
                    "examples": "RESUME: My name is John. I am 30 years old.\nCompany Profile: Startup in Seoul, founded in 2020, with 10 employees.",
                }
            },
        ),
    ]

    # 에이전트 능력 정의 - 스트리밍 지원, 확장 활성화
    capabilities = AgentCapabilities(
        streaming=True,            # 스트리밍 응답 지원
        push_notifications=False,  # 푸시 알림 비활성화
        extensions=extensions      # 정의된 확장들
    )

    # 에이전트 스킬 정의 - 할루시네이션 검사 전문 에이전트
    skill = AgentSkill(
        id="hallucination_check_agent",
        name="Hallucination Check Agent",
        description="AI model output hallucination detection and consistency evaluation agent",
        tags=["hallucination", "fact-check", "consistency"],
        examples=["Tesla was born in Croatia.", "ONNX is faster than TensorRT."],
        input_modes=["application/json"],   # JSON 입력만 지원
        output_modes=["application/json"],  # JSON 출력만 제공
    )

    # 에이전트 카드 정의 - A2A 프로토콜 메타데이터
    agent_card = AgentCard(
        name="hallucination_check_agent",
        description="Advanced hallucination detection agent using consistency evaluation",
        url=f"http://{host}:{port}",  # 서버 접근 URL
        version="0.0.1",
        provider=AgentProvider(
            organization="seocho-data-study", 
            url="https://github.com/cdkkim/data-study"
        ),
        capabilities=capabilities,
        skills=[skill],
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
    )

    # A2A 요청 처리기 구성
    request_handler = DefaultRequestHandler(
        agent_executor=HallucinationCheckExecutor(),  # 할루시네이션 검사 실행기
        task_store=InMemoryTaskStore(),               # 메모리 기반 작업 저장소
    )
    
    # A2A Starlette 애플리케이션 구성
    server = A2AStarletteApplication(
        agent_card=agent_card,        # 에이전트 메타데이터
        http_handler=request_handler  # HTTP 요청 처리기
    )

    # 서버 실행
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main("localhost", 8008)  # 로컬 개발 환경에서 8008 포트로 실행
