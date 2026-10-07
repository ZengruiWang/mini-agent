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
    _SEPARATOR = "─" * 60

    role: Role
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_name: str | None = None
    tool_call_id: str | None = None

    def format(self, index: int) -> str:
        lines = [self._SEPARATOR, f"[{index}] {self.role.value}"]

        if self.content is not None:
            lines.extend(["content:", self.content])
        if self.thinking:
            lines.extend(["thinking:", self.thinking])
        if self.tool_calls:
            lines.append("tool_calls:")
            for tc in self.tool_calls:
                args = ", ".join(f"{k}={v!r}" for k, v in tc.function.arguments.items())
                lines.append(f"  - {tc.function.name}({args})")
                if tc.id:
                    lines.append(f"    id: {tc.id}")
        if self.tool_name:
            lines.append(f"tool_name: {self.tool_name}")
        if self.tool_call_id:
            lines.append(f"tool_call_id: {self.tool_call_id}")

        return "\n".join(lines)

    @staticmethod
    def format_history(messages: list["Message"]) -> str:
        return "\n\n".join(msg.format(i) for i, msg in enumerate(messages))

@dataclass
class StreamChunk:
    content: str | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None  # usually appears once
    done: bool = False