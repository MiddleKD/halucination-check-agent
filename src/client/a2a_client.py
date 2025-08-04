import asyncio
from typing import Any
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (GetTaskRequest, MessageSendParams, SendMessageRequest,
                       SendStreamingMessageRequest, TaskQueryParams)


def print_welcome_message() -> None:
    print("Welcome to the generic A2A client!")
    print("Please enter your query (type 'exit' to quit):")


def get_user_query() -> str:
    return input("\n> ")


async def interact_with_server(client: A2AClient) -> None:
    unique_id = uuid4().hex
    while True:

        user_input = get_user_query()
        if user_input.lower() == "exit":
            print("bye!~")
            break

        send_message_payload: dict[str, Any] = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": user_input}],
                "messageId": uuid4().hex,
                "taskId": unique_id,  # do not work
                "contextId": unique_id,
            },
        }

        try:
            message_request = SendMessageRequest(
                id=unique_id, params=MessageSendParams(**send_message_payload)
            )
            response = await client.send_message(message_request)
            print(response)

            task_id = response.root.id
            task = await client.get_task(
                GetTaskRequest(
                    id=unique_id,
                    params=TaskQueryParams(
                        id="24dba0ca-a12b-41ba-be2f-958212508663", history_length=10
                    ),
                )
            )
            print("Task: ", task)

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
