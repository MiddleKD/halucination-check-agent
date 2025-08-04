from __future__ import annotations as _annotations

from dotenv import load_dotenv

load_dotenv()

from langfuse_trace import init_langfuse

langfuse_cli, observe = init_langfuse()

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agent.context_consistency_agent import context_consistency_agent
from agent.reason_summary_agent import reason_summary_agent
from constant import GRAPH_PERSISTENCE_STATE_PATH_DIR
from dto import (
    HallucinationGraphOutput as GraphOutput,
    HallucinationGraphState as GraphState,
    StateDependencies,
)
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from pydantic_graph.persistence.file import FileStatePersistence


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

    hallucination_score = ctx_result.output.hallucination_score
    ref_url = src_result.output.ref_url

    reason = None
    if ctx.state.return_reason:
        reason = ctx_result.output.reason

    return hallucination_score, ref_url, reason


@dataclass
class GetSrcRoute(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ProsGetSrc | ConsGetSrc:
        if ctx.state.stance_type == "pros":
            return ProsGetSrc()
        elif ctx.state.stance_type == "cons":
            return ConsGetSrc()
        elif ctx.state.stance_type == "both":
            return BothGetSrc()


@dataclass
class ProsGetSrc(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CheckScore:
        hallucination_score, ref_url, reason = await get_src_and_check(ctx, "pros")

        return CheckScore(
            hallucination_score=hallucination_score,
            ref_url=ref_url,
            reason=reason,
        )


@dataclass
class ConsGetSrc(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CheckScore:
        hallucination_score, ref_url, reason = await get_src_and_check(ctx, "cons")

        return CheckScore(
            hallucination_score=hallucination_score,
            ref_url=ref_url,
            reason=reason,
        )


@dataclass
class BothGetSrc(BaseNode[GraphState]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CheckScore:
        tasks = [
            get_src_and_check(ctx, "pros"),
            get_src_and_check(ctx, "cons"),
        ]

        pros_result, cons_result = await asyncio.gather(*tasks)

        return CheckScore(
            hallucination_score=[pros_result[0], cons_result[0]],
            ref_url=[pros_result[1], cons_result[1]],
            reason=[pros_result[2], cons_result[2]]
            if ctx.state.return_reason
            else None,
        )


@dataclass
class CheckScore(BaseNode[GraphState]):
    hallucination_score: float | list[float]
    ref_url: list[str] | list[list[str]]
    reason: str | list[str] | None

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> MergeResult | SummaryReason | GetSrcRoute:

        do_fallback = False
        if ctx.state.stance_type == "both":
            abs_diff = abs(self.hallucination_score[0] - self.hallucination_score[1])
            if abs_diff > ctx.state.score_diff_threshold:
                do_fallback = True
        else:
            if abs(self.hallucination_score - 0.5) < ctx.state.score_diff_threshold:
                do_fallback = True

        if do_fallback and ctx.state.current_fallback < ctx.state.fall_back_limit:
            ctx.state.current_fallback += 1
            return GetSrcRoute()
        else:
            if ctx.state.stance_type == "both":
                ctx.state.ref_url += self.ref_url[0]
                ctx.state.ref_url += self.ref_url[1]
                ctx.state.scores += self.hallucination_score
                if ctx.state.return_reason:
                    ctx.state.reasons += self.reason
            else:
                ctx.state.ref_url += self.ref_url
                ctx.state.scores.append(self.hallucination_score)
                if ctx.state.return_reason:
                    ctx.state.reasons.append(self.reason)

            if ctx.state.return_reason:
                return SummaryReason()
            else:
                return MergeResult(
                    GraphOutput(
                        score=sum(ctx.state.scores) / len(ctx.state.scores),
                        ref_url=ctx.state.ref_url,
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
                ref_url=ctx.state.ref_url,
                reason=reason_summary.output.summary,
            )
        )


@dataclass
class MergeResult(BaseNode[GraphState, None, GraphOutput]):
    output: GraphOutput

    async def run(self, ctx: GraphRunContext[GraphState]) -> End[GraphOutput]:
        return End(self.output)


async def run_graph(query: str | list[str], context_id: str) -> GraphOutput:
    if isinstance(query, str):
        query = [query]

    user_input = query[-1]
    user_history = query[:-1]

    main_graph = Graph(
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

    persistence = FileStatePersistence(
        json_file=Path(f"{GRAPH_PERSISTENCE_STATE_PATH_DIR}/{context_id}.json")
    )
    persistence.set_graph_types(main_graph)

    if snapshot := await persistence.load_next():
        state = snapshot.state
        start_node = None
    else:
        state = GraphState(
            stance_type="cons",
            fall_back_mode=False,
            return_reason=True,
            user_input=user_input,
            user_history=user_history,
        )
        start_node = GetSrcRoute()

    async with main_graph.iter(start_node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()
            if isinstance(node, End):
                result_content = json.dumps(
                    {
                        "score": node.data.score,
                        "ref_url": node.data.ref_url,
                        "reason": node.data.reason,
                    },
                    ensure_ascii=False,
                )
                yield ModelResponse(parts=[TextPart(content=result_content)])
                break
            else:
                yield ModelResponse(parts=[TextPart(content="Node: " + str(node))])


async def main(query: str | list[str], context_id: str) -> str:
    async for response in run_graph(
        query=query,
        context_id=context_id,
    ):
        print(response.parts[0].content, flush=True)
    return response.parts[0].content


def convert_graph_as_agent():
    async def run_graph(user_prompt: list[ModelMessage], _) -> ModelResponse:
        result = await main(user_prompt, "test_id")
        return ModelResponse(parts=[TextPart(content=result)])

    agent = Agent(
        FunctionModel(run_graph, model_name="function_graph_wrapper"), tools=[run_graph]
    )

    return agent


if __name__ == "__main__":
    asyncio.run(main("onnx가 tensorrt 보다 생산성 측면에서 더 효율적입니다.", "test_id"))
