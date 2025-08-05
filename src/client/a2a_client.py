import asyncio
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import Message, MessageSendParams, SendStreamingMessageRequest

def print_welcome_message() -> None:
    print("Welcome to the Halucination Check Agent A2A client!")
    print("Please enter your query (type 'exit' to quit):")

def get_user_query() -> str:
    return input("[User] Enter Your Query\n> ")

def open_input_context_txt() -> str:
    with open("assets/example_context.txt", "r") as f:
        return f.read()

def print_chunk(chunk_map):
    result_dict = chunk_map["result"]

    history = result_dict.get("history")
    status = result_dict.get("status")

    if status:
        print("\tStatus:", status["state"])
        if x:=status.get("message"):
            for part in x["parts"]:
                print(f"\t\tInfo: {part['text']}")

    if history:
        print("\tHistory:")
        for h in history:
            for part in h["parts"]:
                print(f"\t\tInfo: {part['text']}")


async def interact_with_hallucination_check_search_agent(client: A2AClient) -> None:
    context_id = uuid4().hex
    
    user_input = get_user_query()
    if user_input.lower() == "exit":
        print("bye!~")
        return

    send_message_payload: dict[str, Any] = {
        "message": Message(
            message_id=uuid4().hex,
            context_id=context_id,
            role="user",
            parts=[{"type": "text", "text": user_input}],
        ),
        "metadata": {
            "enable_tavily_search_engine/v1": {"enable": True}
        }
    }

    message_request = SendStreamingMessageRequest(
        id=uuid4().hex, params=MessageSendParams(**send_message_payload)
    )

    print("[Halucination(search) Check Agent]: ")
    async for chunk in client.send_message_streaming(message_request):
        chunk_map = chunk.model_dump(mode='json', exclude_none=True)
        print_chunk(chunk_map)

async def interact_with_hallucination_check_context_agent(client: A2AClient, use_example_context: bool = False) -> None:
    context_id = uuid4().hex
    
    while True:

        user_input = get_user_query()
        if user_input.lower() == "exit":
            print("bye!~")
            break

        send_message_payload: dict[str, Any] = {
            "message": Message(
                message_id=uuid4().hex,
                context_id=context_id,
                role="user",
                parts=[{"type": "text", "text": user_input}],
            ),
        }

        if use_example_context:
            send_message_payload.update({
                "metadata": {
                    "set_input_context_explicitly/v1": {"input_context": open_input_context_txt()}
                }
            })

        message_request = SendStreamingMessageRequest(
            id=uuid4().hex, params=MessageSendParams(**send_message_payload)
        )


        print("[Halucination(context) Check Agent]: ")
        async for chunk in client.send_message_streaming(message_request):
            chunk_map = chunk.model_dump(mode='json', exclude_none=True)
            print_chunk(chunk_map)

        if not chunk_map.get("result").get("status").get("state") == "input-required":
            break


async def main(args) -> None:
    print_welcome_message()

    async with httpx.AsyncClient() as httpx_client:
        agent_card = await (
            A2ACardResolver(
                httpx_client=httpx_client,
                base_url=f"http://{args.host}:{args.port}",
            )
        ).get_agent_card()

        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card,
        )

        if args.agent_type == "search":
            print("***Search agent selected***")
            await interact_with_hallucination_check_search_agent(client)
        elif args.agent_type == "context":
            print("***Context agent selected***")
            await interact_with_hallucination_check_context_agent(client, args.use_example_context)
        else:
            raise ValueError(f"Unknown agent type: {args.agent_type}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8008)
    parser.add_argument(
        "--agent-type",
        type=str,
        choices=["context", "search"],
        default="context"
    )
    parser.add_argument("--use-example-context", action="store_true")
    args = parser.parse_args()

    if args.use_example_context and args.agent_type == "search":
        raise ValueError("Cannot use example context with search agent type")

    asyncio.run(main(args))
