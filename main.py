import logging

from dotenv import load_dotenv

from agent import Agent
from providers.openai_provider import OpenAIProvider
from tools.calculator import Calculator
from tools.web_fetch import WebFetch
from tools.web_search import WebSearch

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODEL = "gpt-4o"

if __name__ == "__main__":
    agent = Agent(
        provider=OpenAIProvider(),
        model=MODEL,
        tools=[Calculator(), WebSearch(), WebFetch()],
        system_prompt=(
            "You are a helpful assistant. Use tools when needed to find up-to-date information. "
            "For web questions: call web_search first, then call web_fetch on a result URL "
            "if snippets lack the specific facts the user asked for (e.g. temperatures, prices, scores). "
            "You CAN read full pages with web_fetch — always use it before giving up or telling the user to check links. "
            "After receiving tool results, answer the user's question directly and concisely using that data. "
            "Summarize the relevant facts (e.g. temperatures, dates, numbers) — "
            "do not describe the webpage structure, links, or HTML."
        ),
        stream=False,
    )

    reply = agent.run("what is the weather will be like in the next week for Los Angeles?")