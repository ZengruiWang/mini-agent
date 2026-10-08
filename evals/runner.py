from agent import Agent
from models.message import Message


def run_case(agent: Agent, case: dict) -> tuple[Message, list[Message]]:
    reply = agent.run(case["input"])
    return reply, agent.messages
