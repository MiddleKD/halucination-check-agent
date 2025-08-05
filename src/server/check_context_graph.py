from __future__ import annotations as _annotations

from dotenv import load_dotenv

load_dotenv()

from langfuse_trace import init_langfuse

langfuse_cli = init_langfuse()

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

from agent.context_consistency_agent import context_consistency_agent
from agent.reason_summary_agent import reason_summary_agent
from constant import GRAPH_PERSISTENCE_STATE_PATH_DIR, DUMMY_CONTEXT
from dto import (
    CheckContextGraphOutput as GraphOutput,
    CheckContextGraphState as GraphState,
    StateDependencies,
)
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from pydantic_graph.persistence.file import FileStatePersistence
from typing import AsyncGenerator, Any


async def check_with_input_src(
    ctx: GraphRunContext[GraphState], input_src: str
):
    deps = StateDependencies(
        stance_type="pros", # not used
        return_reason=ctx.state.return_reason,
    )

    ctx_result = await context_consistency_agent.run(
        user_prompt=f"Context: {input_src}\n\nSentence: {ctx.state.user_input}",
        deps=deps,
        message_history=ctx.state.user_history,
    )

    nonsense_score = ctx_result.output.hallucination_score

    reason = None
    if ctx.state.return_reason:
        reason = ctx_result.output.reason

    return nonsense_score, reason


@dataclass
class EnoughContext(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CheckContext | RequestMoreContext:
        if len(ctx.state.input_context) > 100:
            return CheckContext()
        else:
            return RequestMoreContext()


@dataclass
class CheckContext(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CheckScore:
        nonsense_score, reason = await check_with_input_src(
            ctx,
            ctx.state.input_context,
        )

        return CheckScore(
            nonsense_score=nonsense_score,
            reason=reason,
        )


@dataclass
class RequestMoreContext(BaseNode[GraphState]):
    input_context: str = ""
    async def run(self, ctx: GraphRunContext[GraphState]) -> EnoughContext:
        ctx.state.input_context += self.input_context
        return EnoughContext()


@dataclass
class CheckScore(BaseNode[GraphState]):
    nonsense_score: float
    reason: str | None

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> MergeResult | SummaryReason | CheckContext:

        do_fallback = False
        if abs(self.nonsense_score - 0.5) < ctx.state.score_diff_threshold:
            do_fallback = True

        if do_fallback and ctx.state.current_fallback < ctx.state.fall_back_limit:
            ctx.state.current_fallback += 1
            return CheckContext()
        else:
            ctx.state.scores.append(self.nonsense_score)
            if ctx.state.return_reason:
                ctx.state.reasons.append(self.reason)

            if ctx.state.return_reason:
                return SummaryReason()
            else:
                return MergeResult(
                    GraphOutput(
                        score=sum(ctx.state.scores) / len(ctx.state.scores),
                        reason=None,
                    )
                )


@dataclass
class SummaryReason(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> MergeResult:
        reason_summary = await reason_summary_agent.run(
            user_prompt=ctx.state.reasons,
            deps=StateDependencies(return_reason=False),
            message_history=ctx.state.user_history,
        )

        return MergeResult(
            GraphOutput(
                score=sum(ctx.state.scores) / len(ctx.state.scores),
                reason=reason_summary.output.summary,
            )
        )


@dataclass
class MergeResult(BaseNode[GraphState, None, GraphOutput]):
    output: GraphOutput

    async def run(self, ctx: GraphRunContext[GraphState]) -> End[GraphOutput]:
        return End(self.output)


async def run_graph(query: str | list[str], input_context: str, context_id: str) -> AsyncGenerator[dict[str, Any]]:
    if isinstance(query, str):
        query = [query]

    user_input = query[-1]
    user_history = query[:-1]

    main_graph = Graph(
        nodes=(
            EnoughContext,
            CheckContext,
            RequestMoreContext,
            CheckScore,
            SummaryReason,
            MergeResult,
        ),
        name="nonsense_check_graph",
    )

    persistence = FileStatePersistence(
        json_file=Path(f"{GRAPH_PERSISTENCE_STATE_PATH_DIR}/{context_id}.json")
    )
    persistence.set_graph_types(main_graph)

    if snapshot := await persistence.load_next():
        state = snapshot.state
        start_node = RequestMoreContext(
            input_context=f"{user_input}\n\n{input_context}"
        )
    else:
        state = GraphState(
            fall_back_mode=False,
            return_reason=True,
            user_input=user_input,
            user_history=user_history,
            input_context=input_context,
        )
        start_node = EnoughContext()

    with langfuse_cli.start_as_current_span(
        name="nonsense_check_graph",
        input=user_input,
    ) as langfuse_span:
        langfuse_span.update_trace(
            name="Debug Nonsense Check Agent",
            user_id="middlek",
            session_id=context_id,
            tags=["agent", "debug", "nonsense_check"],
            metadata={"email": "middlek@gmail.com"},
            version="1.0.0",
        )

        result_dict = None
        async with main_graph.iter(start_node, state=state, persistence=persistence) as run:
            while True:
                node = await run.next()
                if isinstance(node, End):
                    result_dict = {
                        "score": node.data.score,
                        "reason": node.data.reason,
                    }

                    yield {
                        "input_required": False,
                        "info": "Completed",
                        "content": result_dict,
                    }
                    break
                elif isinstance(node, RequestMoreContext):
                    result_dict = {
                        "info": "Need more information",
                        "content": "판단하기 위한 정보가 부족합니다. 추가 정보를 제공해 주세요."
                    }
                    yield {
                        "input_required": True, 
                        **result_dict,
                    }
                    break
                elif isinstance(node, EnoughContext):
                    yield {
                        "input_required": False,
                        "info": "Checking given information is enough...",
                        "content": None,
                    }
                elif isinstance(node, CheckContext):
                    yield {
                        "input_required": False,
                        "info": "Checking consistency context and query...",
                        "content": None,
                    }
                elif isinstance(node, CheckScore):
                    yield {
                        "input_required": False,
                        "info": "Checking score...",
                        "content": None,
                    }
                elif isinstance(node, SummaryReason):
                    yield {
                        "input_required": False,
                        "info": "Summarizing reason...",
                        "content": None,
                    }
                else:
                    pass

        if result_dict:
            langfuse_span.update_trace(output=result_dict)

async def main(query: str | list[str], input_context: str, context_id: str) -> str:
    async for response in run_graph(
        query=query,
        input_context=input_context,
        context_id=context_id,
    ):
        print(response, flush=True)
    return response


def convert_graph_as_agent():
    async def run_graph(user_prompt: list[ModelMessage], _) -> ModelResponse:
        result = await main(user_prompt, "test_id")
        return ModelResponse(parts=[TextPart(content=json.dumps(result))])

    agent = Agent(
        FunctionModel(run_graph, model_name="function_graph_wrapper"), tools=[run_graph]
    )

    return agent


if __name__ == "__main__":
    asyncio.run(main(
        "홍길동씨는 소프트웨어전공을 살린 직장을 다니고 있으며 현재 삼성헬스케어에 다니고 있습니다.",
        "안녕하세요",
        "test_id"))
    asyncio.run(main(
        "홍길동씨는 소프트웨어전공을 살린 직장을 다니고 있으며 현재 삼성헬스케어에 다니고 있습니다.",
        DUMMY_CONTEXT,
        "test_id"))
