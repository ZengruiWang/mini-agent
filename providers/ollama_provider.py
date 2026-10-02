from collections.abc import Sequence
from typing import Any, Iterator

from ollama import chat, ChatResponse
from ollama import Message as OllamaMessage
from ollama import Tool as OllamaTool

from models.message import Message, Role, StreamChunk, ToolCall, ToolCallFunction
from providers.base_provider import BaseProvider
from tools.base_tool import Tool


class OllamaProvider(BaseProvider):
    def __init__(self):
        pass

    def chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Message:
        response : ChatResponse = chat(
            model=model,
            messages=[self._to_ollama_message(m) for m in messages],
            tools=self._to_ollama_tools(tools),
            think=kwargs.get("think", True),
        )
        return self._from_ollama_message(response.message)

    def stream_chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Iterator[StreamChunk]:
        response = chat(
            model=model,
            messages=[self._to_ollama_message(m) for m in messages],
            tools=self._to_ollama_tools(tools),
            stream=True,
            think=kwargs.get("think", True),
        )

        for chunk in response:
            msg = chunk.message
            yield StreamChunk(
                content=msg.content,
                thinking=msg.thinking,
                tool_calls=self._from_ollama_tool_calls(msg.tool_calls),
                done=chunk.done,
            )

    @staticmethod
    def _from_ollama_message(msg: OllamaMessage) -> Message:
        return Message(
            role=Role(msg.role),
            content=msg.content,
            thinking=msg.thinking,
            tool_calls=OllamaProvider._from_ollama_tool_calls(msg.tool_calls),
        )

    @staticmethod
    def _to_ollama_message(msg: Message) -> OllamaMessage:
        data: dict = {"role": msg.role.value}  # enum -> "user", "assistant", etc.

        if msg.content is not None:
            data["content"] = msg.content
        if msg.thinking is not None:
            data["thinking"] = msg.thinking
        if msg.tool_calls:
            data["tool_calls"] = [
                {
                    **({"id": tc.id} if tc.id else {}),
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        return OllamaMessage.model_validate(data)

    @staticmethod
    def _from_ollama_tool_calls(
            tool_calls: Sequence[Any] | None,
    ) -> list[ToolCall] | None:
        if not tool_calls:
            return None

        return [
            ToolCall(
                id=getattr(tc, "id", None),
                function=ToolCallFunction(
                    name=tc.function.name,
                    arguments=dict(tc.function.arguments),
                ),
            )
            for tc in tool_calls
        ]

    @staticmethod
    def _to_ollama_tools(tools: list[Tool] | None) -> list[OllamaTool] | None:
        if not tools:
            return None
        return [OllamaProvider._to_ollama_tool(t) for t in tools]

    @staticmethod
    def _to_ollama_tool(tool: Tool) -> OllamaTool:
        return OllamaTool.model_validate({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": tool.inputs,
                    "required": list(tool.inputs.keys()),
                },
            },
        })


