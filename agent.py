import logging
from collections.abc import Iterator
from typing import Any

from models.message import Message, Role, StreamChunk, ToolCall
from providers.base_provider import BaseProvider
from tools.base_tool import Tool

logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        provider: BaseProvider,
        model: str,
        *,
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
        messages: list[Message] | None = None,
        stream: bool = False,
        max_turns: int = 10,
        think: bool = True,
    ):
        self.provider = provider
        self.model = model
        self.tools = list(tools) if tools else []
        self._tools_by_name = {tool.name: tool for tool in self.tools}
        self.messages: list[Message] = list(messages) if messages else []
        self.stream = stream
        self.max_turns = max_turns
        self.think = think

        if system_prompt is not None:
            self.messages.insert(0, Message(role=Role.SYSTEM, content=system_prompt))

    def run(self, task: str, *, stream: bool | None = None, **kwargs) -> Message:
        """Send messages to the provider and return one assistant message."""
        logger.info("Task:\n%s", task)
        """Handle one user turn and return the final assistant message."""
        self.messages.append(Message(role=Role.USER, content=task))
        use_stream = self.stream if stream is None else stream
        return self._loop_until_done(stream=use_stream, **kwargs)

    def _loop_until_done(self, *, stream: bool, **kwargs) -> Message:
        for _ in range(self.max_turns):
            reply = self._call_model(stream=stream, **kwargs)
            self.messages.append(reply)

            if not reply.tool_calls:
                logger.info("Messages:\n%s", self.messages)
                return reply

            for tool_call in reply.tool_calls:
                result = self._execute_tool(tool_call)
                self.messages.append(
                    Message(
                        role=Role.TOOL,
                        content=str(result),
                        tool_name=tool_call.function.name,
                        tool_call_id=tool_call.id,
                    )
                )

        logger.info("Messages:\n%s", self.messages)
        raise RuntimeError(f"Agent exceeded {self.max_turns} turns")

    def _call_model(self, *, stream: bool, **kwargs) -> Message:
        provider_kwargs = {"think": kwargs.get("think", self.think), **kwargs}

        if stream:
            chunks = self.provider.stream_chat(
                self.model,
                self.messages,
                tools=self.tools,
                **provider_kwargs,
            )
            reply = self._collect_stream(chunks)
        else:
            reply = self.provider.chat(
                self.model,
                self.messages,
                tools=self.tools,
                **provider_kwargs,
            )
        return reply

    @staticmethod
    def _collect_stream(chunks: Iterator[StreamChunk]) -> Message:
        content = ""
        thinking = ""
        tool_calls = None

        for chunk in chunks:
            if chunk.content:
                content += chunk.content
            if chunk.thinking:
                thinking += chunk.thinking
            if chunk.tool_calls:
                tool_calls = chunk.tool_calls

        return Message(
            role=Role.ASSISTANT,
            content=content or None,
            thinking=thinking or None,
            tool_calls=tool_calls,
        )

    def _execute_tool(self, tool_call: ToolCall) -> Any:
        name = tool_call.function.name
        tool = self._tools_by_name.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")
        return tool.execute(**tool_call.function.arguments)
