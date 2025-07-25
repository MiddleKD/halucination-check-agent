from __future__ import annotations as _annotations

from dotenv import load_dotenv

load_dotenv()

from trace import init_langfuse

langfuse_cli, observe = init_langfuse()

from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from agent.context_consistency_agent import context_consistency_agent
from agent.get_source_agent import get_source_agent
from agent.reason_summary_agent import reason_summary_agent
from dto import GraphOutput, GraphState, StateDependencies
from util import get_uuid

from dataclasses import dataclass

import asyncio
import json


async def get_src_and_check(
    ctx: GraphRunContext[GraphState], stance_type: Literal["pros", "cons"]
):
    deps = StateDependencies(
        stance_type=stance_type,
        return_reason=ctx.state.return_reason,
    )
    src_result = await get_source_agent.run(
        user_prompt=ctx.state.user_input,
        deps=deps,
        message_history=ctx.state.user_history,
    )

    ctx_result = await context_consistency_agent.run(
        user_prompt=f"Context: {src_result.output.summary}\n\nSentence: {ctx.state.user_input}",
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

def convert_graph_as_agent():

    @observe()
    async def run_graph(user_prompt: list[ModelMessage], _) -> GraphOutput:
        
        user_input = user_prompt[-1].parts[0].content
        user_history = user_prompt[:-1]

        state = GraphState(
            stance_type="cons",
            fall_back_mode=False,
            return_reason=True,
            user_input=user_input,
            user_history=user_history,
        )

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

        result = await main_graph.run(GetSrcRoute(), state=state)

        result_content = json.dumps({
            "score": result.output.score,
            "ref_url": result.output.ref_url,
            "reason": result.output.reason,
        }, ensure_ascii=False)

        langfuse_cli.update_current_trace(
            name="Hallucination Check Agent",
            input=user_input,
            output=result_content,
            user_id="middlek",
            session_id=get_uuid(),
            tags=["agent", "hallucination_check"],
            metadata={"email": "middlek@gmail.com"},
            version="1.0.0"
        )

        return ModelResponse(parts=[TextPart(content=result_content)])

    agent = Agent(
        FunctionModel(run_graph, model_name="function_graph_wrapper"),
        tools=[run_graph]
    )

    return agent

@observe()
async def debug(user_input: str, user_history: list[ModelMessage]):
    state = GraphState(
        stance_type="both",
        fall_back_mode=True,
        return_reason=True,
        user_input=user_input,
        user_history=user_history,
    )

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

    async with main_graph.iter(
        GetSrcRoute(), state=state
    ) as run:
        async for node in run:
            print("Node:", node)
    print("Final output:", run.result.output)

    result_content = json.dumps({
        "score": run.result.output.score,
        "ref_url": run.result.output.ref_url,
        "reason": run.result.output.reason,
    }, ensure_ascii=False)

    langfuse_cli.update_current_trace(
        name="Debug Hallucination Check Agent",
        input=user_input,
        output=result_content,
        user_id="middlek",
        session_id=get_uuid(),
        tags=["agent", "debug", "hallucination_check"],
        metadata={"email": "middlek@gmail.com"},
        version="1.0.0"
    )
    
if __name__ == "__main__":
    asyncio.run(debug(
        user_input="onnx가 생산성 측면에서 더 효율적입니다.",
        user_history=[ModelResponse(parts=[TextPart(content="tensorrt와 onnx 중 뭐가 더 효율적일까?")])],
    ))
