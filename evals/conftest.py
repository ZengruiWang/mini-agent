from collections.abc import Callable

import pytest
from dotenv import load_dotenv

from agent import Agent
from providers.openai_provider import OpenAIProvider
from resources.loader import load_system_prompt
from tools.calculator import Calculator

load_dotenv()


@pytest.fixture
def make_agent() -> Callable[..., Agent]:
    def _make(**overrides) -> Agent:
        defaults = {
            "provider": OpenAIProvider(),
            "model": "gpt-4o",
            "tools": [Calculator()],
            "system_prompt": load_system_prompt(),
            "stream": False,
        }
        defaults.update(overrides)
        return Agent(**defaults)

    return _make
