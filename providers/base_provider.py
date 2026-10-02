from abc import ABC, abstractmethod
from collections.abc import Iterator

from models.message import Message, StreamChunk
from tools.base_tool import Tool


class BaseProvider(ABC):
    @abstractmethod
    def chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Message:
        """Wait for full response."""

    @abstractmethod
    def stream_chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Iterator[StreamChunk]:
        """Yield partial chunks as they arrive."""