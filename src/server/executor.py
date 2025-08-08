"""
Hallucination Check Executor - A2A 프로토콜 메인 실행기

Agent-to-Agent 프로토콜을 통해 할루시네이션 검사 요청을 처리하는 핵심 실행기입니다.
두 가지 실행 모드를 지원합니다:
1. Search Graph: Tavily 검색을 통한 컨텍스트 수집 후 평가
2. Context Graph: 명시적으로 제공된 컨텍스트를 사용한 평가

주요 기능:
- A2A 프로토콜 확장(Extension) 기반 실행 모드 선택
- 스트리밍 응답 지원
- 작업 상태 추적 및 업데이트
- JSON 형태 결과 반환
"""

import json
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    UnsupportedOperationError, 
    InvalidParamsError, 
    TaskState, 
    Part, 
    TextPart
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from check_search_graph import run_graph as check_search_graph_run
from check_context_graph import run_graph as check_context_graph_run
from constant import (
    A2A_SEARCH_ENGINE_EXTENSION_URI, 
    A2A_SET_INPUT_CONTEXT_EXTENSION_URI
)


class HallucinationCheckExecutor(AgentExecutor):
    """할루시네이션 검사 실행기 - A2A 프로토콜 메인 처리 클래스"""
    def __init__(self):
        """실행기 초기화 - 두 가지 그래프 실행 함수 등록"""
        self.run_search_graph = check_search_graph_run     # Tavily 검색 기반 평가
        self.run_context_graph = check_context_graph_run   # 명시적 컨텍스트 기반 평가

    async def _resolve_graph_with_extension(
        self, 
        context: RequestContext, 
        event_queue: EventQueue
    ) -> dict[str, Any]:
        """
        A2A 확장(Extension)을 분석하여 적절한 실행 그래프를 선택합니다.
        
        Args:
            context: A2A 요청 컨텍스트 (확장 메타데이터 포함)
            event_queue: 이벤트 큐 (작업 상태 업데이트용)
        
        Returns:
            dict: 선택된 그래프와 실행 인자들
            
        Raises:
            ServerError: 검색과 명시적 컨텍스트 확장이 동시에 활성화된 경우
        """
        use_search_graph = False
        use_context_graph = False

        # 검색 엔진 확장 확인
        if search_extension := context.metadata.get(A2A_SEARCH_ENGINE_EXTENSION_URI):
            if search_extension["enable"]:
                use_search_graph = True
            else:
                use_context_graph = True
        
        # 명시적 컨텍스트 확장 확인
        input_context_map: dict = {}
        if context_extension := context.metadata.get(A2A_SET_INPUT_CONTEXT_EXTENSION_URI):
            input_context_map: dict = context_extension
            use_context_graph = True

        # 상호 배타적 확장 검증
        if use_search_graph and use_context_graph:
            raise ServerError(
                error=InvalidParamsError(
                    message="검색 엔진과 명시적 컨텍스트 확장은 동시에 사용할 수 없습니다."
                )
            )

        # 사용자 입력 및 작업 준비
        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        # 선택된 그래프에 따른 실행 계획 반환
        if use_search_graph:
            return {
                "graph": self.run_search_graph,
                "task": task,
                "args": {
                    "query": query,
                    "context_id": task.context_id,
                }
            }
        else:
            return {
                "graph": self.run_context_graph,
                "task": task,
                "args": {
                    "query": query,
                    "input_context": input_context_map.get("input_context", ""),
                    "context_id": task.context_id,
                }
            }

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        할루시네이션 검사를 실행하고 결과를 스트리밍으로 반환합니다.
        
        Args:
            context: A2A 요청 컨텍스트
            event_queue: 이벤트 큐 (상태 업데이트용)
        """
        # 확장을 분석하여 실행 계획 수립
        run_plan = await self._resolve_graph_with_extension(context, event_queue)

        graph_run_main = run_plan["graph"]  # 실행할 그래프 함수
        task = run_plan["task"]             # A2A 작업 객체
        args = run_plan["args"]             # 그래프 실행 인자

        # 작업 상태 업데이터 초기화
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        # 그래프 실행 및 스트리밍 응답 처리
        async for result in graph_run_main(**args):
            if result.get("input_required") == True:
                # 추가 입력 요구 상태
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        text=result.get("content"),
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=True
                )
            elif result.get("info") == "Completed":
                # 최종 결과 반환 - JSON 형태로 아티팩트 저장
                content_json = json.dumps(result.get("content"), ensure_ascii=False)
                
                # 결과를 아티팩트로 저장
                await updater.add_artifact(
                    [Part(root=TextPart(text=content_json))],
                    name='agent_result',
                )
                
                # 완료 상태로 업데이트
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(
                        text=content_json,
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=True
                )
            else:
                # 중간 진행 상황 업데이트
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        text=result.get("info"),
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=False
                )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """작업 취소 - 현재 지원되지 않음"""
        raise ServerError(error=UnsupportedOperationError())
