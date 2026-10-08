import logging

from dotenv import load_dotenv

from agent import Agent
from providers.openai_provider import OpenAIProvider
from resources.loader import load_system_prompt
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
        system_prompt=load_system_prompt(),
        stream=False,
    )

    reply = agent.run("what is the return policy for Costco?")