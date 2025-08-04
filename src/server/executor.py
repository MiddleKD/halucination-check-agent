import json
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import UnsupportedOperationError, TaskState
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError

from hallucination_check_graph import run_graph as hallucination_check_graph_run
from nonsense_check_graph import run_graph as nonsense_check_graph_run

class HallucinationCheckExecutor(AgentExecutor):
    def __init__(self):
        self.run_graph = hallucination_check_graph_run

    async def execute(self, context: RequestContext, evenvt_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await evenvt_queue.enqueue_event(task)
        updater = TaskUpdater(evenvt_queue, task.id, task.context_id)
        

        async for result in self.run_graph(query, context.message.context_id):
            if result.get("input_required") == True:
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        text=result.get("content"),
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=False
                )
            elif result.get("info") == "Completed":
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(
                        text=json.dumps(result.get("content")),
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


class NonsenseCheckExecutor(AgentExecutor):
    def __init__(self):
        self.run_graph = nonsense_check_graph_run

    async def execute(self, context: RequestContext, evenvt_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task
        input_context = context.metadata.get("input_context")

        if not task:
            task = new_task(context.message)
            await evenvt_queue.enqueue_event(task)
        updater = TaskUpdater(evenvt_queue, task.id, task.context_id)
        

        async for result in self.run_graph(query, input_context, context.message.context_id):
            if result.get("input_required") == True:
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        text=result.get("content"),
                        context_id=task.context_id,
                        task_id=task.id,
                    ),
                    final=False
                )
            elif result.get("info") == "Completed":
                await updater.update_status(
                    TaskState.completed,
                    new_agent_text_message(
                        text=json.dumps(result.get("content")),
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
