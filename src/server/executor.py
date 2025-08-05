import json
from typing import Any
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import UnsupportedOperationError, InvalidParamsError, TaskState, Part, TextPart
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from check_search_graph import run_graph as check_search_graph_run
from check_context_graph import run_graph as check_context_graph_run

from constant import A2A_SEARCH_ENGINE_EXTENSION_URI, A2A_SET_INPUT_CONTEXT_EXTENSION_URI


class HallucinationCheckExecutor(AgentExecutor):
    def __init__(self):
        self.run_search_graph = check_search_graph_run
        self.run_context_graph = check_context_graph_run

    async def _resolve_graph_with_extension(self, context: RequestContext, event_queue: EventQueue) -> dict[str, Any]:
        use_search_graph = False
        use_context_graph = False

        if x := context.metadata.get(A2A_SEARCH_ENGINE_EXTENSION_URI):
            if x["enable"]:
                use_search_graph = True
            else:
                use_context_graph = True
        
        input_context_map:dict = {}
        if x := context.metadata.get(A2A_SET_INPUT_CONTEXT_EXTENSION_URI):
            input_context_map:dict = x
            use_context_graph = True

        if use_search_graph and use_context_graph:
            raise ServerError(error=InvalidParamsError(message="if input context is provided explicitly, cannot use search engine extension."))

        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
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
        run_plan = await self._resolve_graph_with_extension(context, event_queue)

        graph_run_main = run_plan["graph"]
        task = run_plan["task"]
        args = run_plan["args"]

        updater = TaskUpdater(event_queue, task.id, task.context_id)

        async for result in graph_run_main(**args):
            if result.get("input_required") == True:
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
                await updater.add_artifact(
                        [Part(root=TextPart(text=json.dumps(result.get("content"), ensure_ascii=False)))],
                        name='agent_result',
                    )
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(
                        text=json.dumps(result.get("content"), ensure_ascii=False),
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=True
                )
            else:
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
        raise ServerError(error=UnsupportedOperationError())
