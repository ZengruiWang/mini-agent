import logging

from agent import Agent
from providers.ollama_provider import OllamaProvider
from tools.calculator import Calculator

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODEL = "qwen3:8b"

if __name__ == "__main__":
    agent = Agent(
        provider=OllamaProvider(),
        model=MODEL,
        tools=[Calculator()],
        system_prompt="You are a helpful assistant. Use tools when needed.",
        stream=False,
    )

    reply = agent.run("what is the volume of earth?")
    print(reply.content)
