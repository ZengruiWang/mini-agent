import json
from collections.abc import Iterator, Sequence
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageParam, ChatCompletionToolParam

from models.message import Message, Role, StreamChunk, ToolCall, ToolCallFunction
from providers.base_provider import BaseProvider
from tools.base_tool import Tool


class OpenAIProvider(BaseProvider):
    def __init__(self):
        self.client = OpenAI()

    def chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Message:
        request: dict[str, Any] = {
            "model": model,
            "messages": [self._to_openai_message(m) for m in messages],
        }
        openai_tools = self._to_openai_tools(tools)
        if openai_tools is not None:
            request["tools"] = openai_tools

        completion = self.client.chat.completions.create(**request)
        return self._from_openai_message(completion.choices[0].message)

    def stream_chat(self, model: str, messages: list[Message], tools: list[Tool] | None = None, **kwargs) -> Iterator[
        StreamChunk]:
        request: dict[str, Any] = {
            "model": model,
            "messages": [self._to_openai_message(m) for m in messages],
            "stream": True,
        }
        openai_tools = self._to_openai_tools(tools)
        if openai_tools is not None:
            request["tools"] = openai_tools

        tool_calls_accum: dict[int, dict[str, str]] = {}

        for chunk in self.client.chat.completions.create(**request):
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                yield StreamChunk(content=delta.content)

            if delta.tool_calls:
                OpenAIProvider._accumulate_tool_call_delta(tool_calls_accum, delta.tool_calls)

            if choice.finish_reason is not None:
                assembled = OpenAIProvider._tool_calls_from_accumulated(tool_calls_accum)
                if assembled:
                    yield StreamChunk(tool_calls=assembled, done=True)
                else:
                    yield StreamChunk(done=True)

    @staticmethod
    def _to_openai_message(message: Message) -> ChatCompletionMessageParam:
        match message.role:
            case Role.SYSTEM | Role.USER:
                data: dict[str, Any] = {"role": message.role.value}
                if message.content is not None:
                    data["content"] = message.content
                return data  # type: ignore[return-value]

            case Role.ASSISTANT:
                data = {"role": "assistant"}
                if message.content is not None:
                    data["content"] = message.content
                if message.tool_calls:
                    data["tool_calls"] = OpenAIProvider._to_openai_tool_calls(message.tool_calls)
                return data  # type: ignore[return-value]

            case Role.TOOL:
                return {
                    "role": "tool",
                    "content": message.content or "",
                    "tool_call_id": message.tool_call_id or "",
                }  # type: ignore[return-value]

            case _:
                raise ValueError(f"Unsupported role for OpenAI: {message.role}")

    @staticmethod
    def _to_openai_tool_calls(tool_calls: list[ToolCall]) -> list[dict[str, Any]]:
        return [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": json.dumps(tc.function.arguments),
                },
            }
            for tc in tool_calls
            if tc.id is not None
        ]

    @staticmethod
    def _to_openai_tools(tools: list[Tool] | None) -> list[ChatCompletionToolParam] | None:
        if not tools:
            return None
        return [OpenAIProvider._to_openai_tool(t) for t in tools]

    @staticmethod
    def _to_openai_tool(tool: Tool) -> ChatCompletionToolParam:
        return {
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
        }  # type: ignore[return-value]

    @staticmethod
    def _from_openai_message(msg: ChatCompletionMessage) -> Message:
        return Message(
            role=Role.ASSISTANT,
            content=msg.content,
            tool_calls=OpenAIProvider._from_openai_tool_calls(msg.tool_calls),
        )

    @staticmethod
    def _from_openai_tool_calls(tool_calls: Sequence[Any] | None) -> list[ToolCall] | None:
        if not tool_calls:
            return None

        parsed: list[ToolCall] = []
        for tc in tool_calls:
            if getattr(tc, "type", None) != "function":
                continue

            arguments = tc.function.arguments
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            parsed.append(
                ToolCall(
                    id=tc.id,
                    function=ToolCallFunction(
                        name=tc.function.name,
                        arguments=dict(arguments),
                    ),
                )
            )

        return parsed or None

    @staticmethod
    def _accumulate_tool_call_delta(
        accumulated: dict[int, dict[str, str]],
        tool_calls: Sequence[Any],
    ) -> None:
        for tc in tool_calls:
            entry = accumulated.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
            if tc.id:
                entry["id"] = tc.id
            if tc.function:
                if tc.function.name:
                    entry["name"] += tc.function.name
                if tc.function.arguments:
                    entry["arguments"] += tc.function.arguments

    @staticmethod
    def _tool_calls_from_accumulated(accumulated: dict[int, dict[str, str]]) -> list[ToolCall] | None:
        if not accumulated:
            return None

        parsed: list[ToolCall] = []
        for index in sorted(accumulated):
            entry = accumulated[index]
            arguments = entry["arguments"]
            if arguments:
                try:
                    parsed_args = json.loads(arguments)
                except json.JSONDecodeError:
                    parsed_args = {}
            else:
                parsed_args = {}

            parsed.append(
                ToolCall(
                    id=entry["id"] or None,
                    function=ToolCallFunction(
                        name=entry["name"],
                        arguments=dict(parsed_args),
                    ),
                )
            )

        return parsed or None