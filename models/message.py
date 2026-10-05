from dataclasses import dataclass
from enum import Enum
from typing import Any

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass
class ToolCallFunction:
    name: str
    arguments: dict[str, Any]

@dataclass
class ToolCall:
    function: ToolCallFunction
    id: str | None = None

@dataclass
class Message:
    role: Role
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_name: str | None = None

@dataclass
class StreamChunk:
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None  # usually appears once
    done: bool = False