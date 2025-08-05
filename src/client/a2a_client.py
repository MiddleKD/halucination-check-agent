import asyncio
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (GetTaskRequest, MessageSendParams, Message,
                       SendStreamingMessageRequest, TaskQueryParams)


def print_welcome_message() -> None:
    print("Welcome to the Halucination Check Agent A2A client!")
    print("Please enter your query (type 'exit' to quit):")


def get_user_query() -> str:
    return input("\n> ")


async def interact_with_server(client: A2AClient) -> None:
    # breakpoint()
    while True:

        user_input = get_user_query()
        if user_input.lower() == "exit":
            print("bye!~")
            break

        send_message_payload: dict[str, Any] = {
            "message": Message(
                message_id=uuid4().hex,
                role="user",
                parts=[{"type": "text", "text": user_input}],
            ),
            "metadata": {
                "enable_tavily_search_engine/v1": {"enable": True}
            }
        }

        try:
            message_request = SendStreamingMessageRequest(
                id=uuid4().hex, params=MessageSendParams(**send_message_payload)
            )

            async for chunk in client.send_message_streaming(message_request):
                print(chunk)


        except Exception as e:
            print(f"An error occurred: {e}")


async def main() -> None:
    print_welcome_message()

    async with httpx.AsyncClient() as httpx_client:
        agent_card = await (
            A2ACardResolver(
                httpx_client=httpx_client,
                base_url="http://localhost:8008",
            )
        ).get_agent_card()

        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card,
        )
        await interact_with_server(client)


if __name__ == "__main__":
    asyncio.run(main())
