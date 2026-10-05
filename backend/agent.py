import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from models import ChatContext, ChatReply
from tools import get_customer_context, get_product_stock, lookup_product_information, search_products
from audit import record

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE.parent.parent / ".env")


def make_agent() -> Agent[ChatContext, ChatReply]:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the project-root .env file")
    client = AsyncOpenAI(api_key=key, base_url="https://api.portkey.ai/v1")
    model = OpenAIChatModel("gpt-5.6-luna", provider=OpenAIProvider(openai_client=client))
    instructions = (HERE / "prompts" / "prompt.md").read_text(encoding="utf-8")
    agent = Agent(model, deps_type=ChatContext, output_type=ChatReply, instructions=instructions, retries=1)
    agent.tool(search_products)
    agent.tool(lookup_product_information)
    agent.tool(get_product_stock)
    agent.tool(get_customer_context)
    return agent


async def run_chat(message: str, context: ChatContext) -> ChatReply:
    record(None, "chat message received", f"chars={len(message)}")
    recent = "\n".join(f"{item['role']}: {item['content']}" for item in context.recent_messages)
    context_message = f"\nRecent conversation context (use only to resolve references):\n{recent}" if recent else ""
    try:
        result = await make_agent().run(message + context_message, deps=context)
    except Exception as exc:
        record(None, "agent run", type(exc).__name__, "agent error")
        raise
    record(None, "agent run", f"reply chars={len(result.output.reply)}, products={len(result.output.products)}", "structured reply returned")
    return result.output
