# 🤖 Hallucination Check Agent

![Agent Flow Diagram](assets/agent_flow.png)

![Pydantic AI](https://img.shields.io/badge/agent%20fw-pydantic_ai-pink.svg)
![Langfuse](https://img.shields.io/badge/observability-langfuse-red.svg)
![A2A Protocol](https://img.shields.io/badge/protocol-A2A-green.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Advanced NLI-based hallucination detection agent for LLM outputs**

LLM 응답 내 할루시네이션(사실과 다른 정보)과 자기모순 여부를 검출하는 평가 에이전트입니다. Natural Language Inference(NLI) 기반으로 AI 모델 응답의 할루시네이션을 탐지하는 고성능 평가 시스템으로, Agent-to-Agent(A2A) 프로토콜을 통해 서비스됩니다.

## ✨ Key Features

🔍 **Dual Evaluation Modes**
- **Search Mode**: Tavily 검색을 통한 자동 컨텍스트 수집 및 평가
- **Context Mode**: 사용자 제공 컨텍스트 기반 직접 평가

🤖 **Multi-Agent Architecture**  
- **GPT-4o**: 정확한 NLI 평가 및 한국어 요약
- **GPT-3.5-turbo**: 효율적인 검색 및 컨텍스트 수집

🌐 **A2A Protocol Integration**
- 표준화된 Agent-to-Agent 프로토콜 지원
- 확장 가능한 플러그인 아키텍처
- 실시간 스트리밍 응답

📊 **Production Ready**
- Langfuse 기반 완전한 관찰 가능성
- 자동 재시도 및 안정성 보장
- 상세한 성능 메트릭 및 추적

---

## 🔧 Basic Concepts

### NLI 기반 할루시네이션 검출

이 시스템은 **Natural Language Inference(NLI)** 접근법을 사용하여 할루시네이션을 검출합니다:

1. **컨텍스트 수집**: Tavily 검색 또는 사용자 제공 컨텍스트
2. **일관성 평가**: 컨텍스트와 검증할 문장 간의 논리적 관계 분석
3. **점수 산출**: 0.0(일치) ~ 1.0(모순) 사이의 할루시네이션 점수
4. **이유 제공**: 평가 결과에 대한 상세한 설명

### 두 가지 평가 모드

**검색 모드 (Search Mode)**:
- Tavily API를 통해 자동으로 관련 정보 검색
- 찬성(pros)/반대(cons) 관점 지원
- 일반적인 사실 확인에 적합

**컨텍스트 모드 (Context Mode)**:
- 사용자가 직접 참조 컨텍스트 제공
- 도메인별 특화 평가 가능
- 더 빠른 응답 시간

---

## 🤖 Agent Types

### 1. Get Source Agent (GPT-3.5-turbo)
- **역할**: Tavily 검색을 통한 컨텍스트 수집 및 요약
- **입력**: 검증할 질의 + 검색 관점(pros/cons)
- **출력**: 요약된 컨텍스트 + 참조 URL 목록

### 2. Context Consistency Agent (GPT-4o)  
- **역할**: NLI 기반 할루시네이션 평가
- **입력**: 컨텍스트 + 검증할 문장
- **출력**: 할루시네이션 점수(0.0-1.0) + 평가 이유

### 3. Reason Summary Agent (GPT-4o)
- **역할**: 다중 평가 결과의 한국어 요약
- **입력**: 여러 평가 이유 목록
- **출력**: 통합된 한국어 요약 (300자 이내)

---

## 📁 Project Structure

```
halucination_check_agent/
├── src/
│   ├── client/                          #
│   │   ├── a2a_client.py               # CLI A2A 클라이언트
│   │   └── fasta2a_client.py           # FastA2A(pydantic-ai) 클라이언트
│   └── server/                         
│       ├── agent/                      # 에이전트
│       │   ├── context_consistency_agent.py  # NLI 기반 일관성 평가
│       │   ├── get_source_agent.py           # 검색 기반 컨텍스트 수집
│       │   └── reason_summary_agent.py       # 평가 결과 한국어 요약
│       ├── app_a2a.py                  # A2A 프로토콜 서버
│       ├── app_fasta2a.py              # FastA2A(pydantic-ai) 서버
│       ├── check_search_graph.py       # 검색 그래프 실행 로직
│       ├── check_context_graph.py      # 컨텍스트 그래프 실행 로직
│       ├── executor.py                 # A2A 요청 처리 실행기
│       ├── dto.py                      # 데이터 타입 객체
│       ├── constant.py                 # 설정 상수
│       ├── langfuse_trace.py           # Langfuse 추적 설정
│       └── util.py                     
├── langfuse/                           # Langfuse 스택
│   ├── docker-compose.yml              # Langfuse 도커 설정
│   └── ...                             
├── assets/                             
│   ├── agent_flow.png                  
│   ├── what_is_nli.md                  # NLI 개념 설명 문서
│   └── example_context.txt             # 예시 컨텍스트
├── state/                              # 그래프 상태 저장소(for human in the loop)
├── .env.example                        # 환경변수 템플릿
├── pyproject.toml                      
├── uv.lock                            
└── README.md                          
```
---

## 🚀 Quick Start

### 1. 📦 Installation

```bash
git clone https://github.com/middlek/halucination_check_agent.git
cd halucination_check_agent
uv venv
source .venv/bin/activate
uv sync
```

### 2. 🔧 Setup Observability

```bash
cd langfuse
docker compose up -d
```

> 📌 Langfuse runs at `http://localhost:3000` - Create project and get API keys

### 3. ⚙️ Environment Configuration

```bash
# Copy and configure environment variables
cp .env.example .env

# Edit .env with your API keys:
# ✅ OpenAI API key (required)
# ✅ Tavily API key (required for search mode)  
# ✅ Langfuse keys (required for observability)
```

### 4. 🎯 Launch Server

**A2A Protocol Server (Recommended):**
```bash
uv run src/server/app_a2a.py
```

> 🌐 Test at `http://localhost:8008/.well-known/agent-card.json` after server startup

**FastA2A Server (Simplified):**
```bash
uv run src/server/app_fasta2a.py
```

> 🌐 Test at `http://localhost:8008/docs` after server startup

---

## 📡 A2A Client Usage Guide

### 🧪 Test with Built-in CLI Client

Use the included CLI client for quick testing:

```bash
# 🔍 Search mode evaluation
uv run src/client/a2a_client.py --agent-type search

# 📝 Context mode evaluation
uv run src/client/a2a_client.py --agent-type context

# 📄 Use example context file
uv run src/client/a2a_client.py --agent-type context --use-example-context
```

### 💻 Custom A2A Client Implementation

```python
import asyncio
from uuid import uuid4
import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import Message, MessageSendParams, SendStreamingMessageRequest

class HallucinationCheckClient:
    def __init__(self, host="localhost", port=8008):
        self.base_url = f"http://{host}:{port}"
        
    async def check_with_search(self, statement):
        """검색 기반 할루시네이션 검사"""
        async with httpx.AsyncClient() as httpx_client:
            # A2A 에이전트 카드 가져오기
            agent_card = await A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.base_url,
            ).get_agent_card()

            # A2A 클라이언트 생성
            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card,
            )

            # 메시지 페이로드 구성
            context_id = uuid4().hex
            send_message_payload = {
                "message": Message(
                    message_id=uuid4().hex,
                    context_id=context_id,
                    role="user",
                    parts=[{"type": "text", "text": statement}],
                ),
                "metadata": {
                    "enable_tavily_search_engine/v1": {"enable": True}
                }
            }

            # 스트리밍 메시지 요청
            message_request = SendStreamingMessageRequest(
                id=uuid4().hex, 
                params=MessageSendParams(**send_message_payload)
            )

            # 응답 처리
            async for chunk in client.send_message_streaming(message_request):
                chunk_data = chunk.model_dump(mode='json', exclude_none=True)
                # 진행 상황 출력
                if status := chunk_data.get("result", {}).get("status"):
                    print(f"Status: {status['state']}")
                    
                # 완료된 결과 반환
                if chunk_data.get("result", {}).get("status", {}).get("state") == "completed":
                    return chunk_data["result"]

    async def check_with_context(self, statement, context):
        """컨텍스트 기반 할루시네이션 검사"""
        async with httpx.AsyncClient() as httpx_client:
            agent_card = await A2ACardResolver(
                httpx_client=httpx_client,
                base_url=self.base_url,
            ).get_agent_card()

            client = A2AClient(
                httpx_client=httpx_client,
                agent_card=agent_card,
            )

            context_id = uuid4().hex
            send_message_payload = {
                "message": Message(
                    message_id=uuid4().hex,
                    context_id=context_id,
                    role="user",
                    parts=[{"type": "text", "text": statement}],
                ),
                "metadata": {
                    "set_input_context_explicitly/v1": {"input_context": context}
                }
            }

            message_request = SendStreamingMessageRequest(
                id=uuid4().hex, 
                params=MessageSendParams(**send_message_payload)
            )

            async for chunk in client.send_message_streaming(message_request):
                chunk_data = chunk.model_dump(mode='json', exclude_none=True)
                if chunk_data.get("result", {}).get("status", {}).get("state") == "completed":
                    return chunk_data["result"]

# 📋 Usage Example
async def main():
    client = HallucinationCheckClient()

    # 🔍 Search-based evaluation
    print("=== 🔍 Search-based Evaluation ===")
    result1 = await client.check_with_search("Tesla invented the light bulb")
    print(f"Result: {result1}")

    # 📝 Context-based evaluation
    print("\n=== 📝 Context-based Evaluation ===")
    context = "Tesla was known for AC electrical systems and wireless technology."
    result2 = await client.check_with_context("Tesla invented the light bulb", context)
    print(f"Result: {result2}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 References

* [SelfCheckAgent(25.02)](https://arxiv.org/html/2502.01812v1)
* [SelfCheckGPT(23.10)](https://github.com/potsawee/selfcheckgpt)
* [NLI 기반 문장 자기모순 및 할루시네이션 평가 방법 요약](assets/what_is_nli.md)

