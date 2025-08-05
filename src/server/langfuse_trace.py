import os
import base64
import logfire

from langfuse import get_client


def init_langfuse():
    langfuse_cli = get_client()

    if langfuse_cli.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")

    langfuse_auth = base64.b64encode(
        f"{os.getenv("LANGFUSE_PUBLIC_KEY")}:{os.getenv("LANGFUSE_SECRET_KEY")}".encode()
    ).decode()
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
    # logfire.instrument_asyncpg()

    return langfuse_cli
