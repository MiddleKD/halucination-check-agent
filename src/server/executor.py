from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import UnsupportedOperationError
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from dto import GraphState
from graph import (BothGetSrc, CheckScore, ConsGetSrc, GetSrcRoute, Graph,
                   MergeResult, ProsGetSrc, SummaryReason)


class HallucinationCheckExecutor(AgentExecutor):
    def __init__(self):
        self.graph = Graph(
            nodes=(
                GetSrcRoute,
                ProsGetSrc,
                ConsGetSrc,
                BothGetSrc,
                CheckScore,
                SummaryReason,
                MergeResult,
            ),
            name="hallucination_check_graph",
        )

    async def execute(self, context: RequestContext, evenvt_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task

        if not task:
            task = new_task(context.message)
            await evenvt_queue.enqueue_event(task)
        updater = TaskUpdater(evenvt_queue, task.id, task.context_id)

        state = GraphState(
            stance_type="cons",
            fall_back_mode=False,
            return_reason=True,
            user_input=query,
            user_history=context.message_history,
        )
        from pydantic_graph.persistence.in_mem import SimpleStatePersistence

        persistence = SimpleStatePersistence()
        self.graph.iter_from_persistence

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
