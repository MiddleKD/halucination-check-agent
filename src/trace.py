import os
import logfire
from langfuse import get_client, observe

def init_langfuse():
    langfuse_cli = get_client()

    if langfuse_cli.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")

    os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:3000'
    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)
    # logfire.instrument_asyncpg()

    return langfuse_cli, observe
