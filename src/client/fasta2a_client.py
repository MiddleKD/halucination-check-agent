import asyncio
from typing import Any
from uuid import uuid4

import httpx
from fasta2a.client import A2AClient
from fasta2a.schema import Message, TextPart


def print_welcome_message() -> None:
    print("Welcome to the generic A2A client!")
    print("Please enter your query (type 'exit' to quit):")


def get_user_query() -> str:
    return input("\n> ")


async def interact_with_server(client: A2AClient) -> None:
    while True:
        user_input = get_user_query()
        if user_input.lower() == "exit":
            print("bye!~")
            break

        message = Message(
            role="user",
            parts=[TextPart(kind="text", text=user_input)],
            kind="message",
            message_id=uuid4().hex,
        )

        resume_metadata: dict[str, Any] = {"resume": "This is dummy resume"}

        # try:
        response = await client.send_message(
            message,
        )

        print("Agent: ", response)

        task_id = response["result"]["id"]
        task = await client.get_task(task_id)
        print("Task: ", task)

        # except Exception as e:
        #     print(f"An error occurred: {e}")


async def main() -> None:
    print_welcome_message()
    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(base_url="http://localhost:8008", http_client=httpx_client)
        await interact_with_server(client)


if __name__ == "__main__":
    asyncio.run(main())
