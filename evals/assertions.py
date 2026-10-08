from models.message import Message, Role
from evals.parsing import extract_numbers, normalize_numeric_text


def tools_called(messages: list[Message]) -> list[str]:
    names: list[str] = []
    for message in messages:
        if message.tool_calls:
            for tool_call in message.tool_calls:
                names.append(tool_call.function.name)
    return names


def assert_tools_called(messages: list[Message], expected: list[str]) -> None:
    called = tools_called(messages)
    for tool in expected:
        assert tool in called, f"Expected tool {tool!r} to be called, got {called!r}"


def assert_tools_not_called(messages: list[Message], forbidden: list[str]) -> None:
    called = tools_called(messages)
    for tool in forbidden:
        assert tool not in called, f"Expected tool {tool!r} not to be called, got {called!r}"


def assert_answer_contains(reply: Message, text: str) -> None:
    content = reply.content or ""
    if text in content:
        return

    normalized_content = normalize_numeric_text(content)
    normalized_text = normalize_numeric_text(text)
    if normalized_text and normalized_text in normalized_content:
        return

    assert False, f"Expected answer to contain {text!r}, got {content!r}"


def _within_tolerance(actual: float, expected: float, tolerance: float) -> bool:
    if expected == 0:
        return abs(actual) <= tolerance
    return abs(actual - expected) / abs(expected) <= tolerance


def assert_answer_close_to(
    reply: Message,
    expected: float,
    *,
    tolerance: float = 0.01,
) -> None:
    content = reply.content or ""
    numbers = extract_numbers(content)
    assert numbers, f"Expected a numeric answer close to {expected}, got no numbers in {content!r}"

    for value in numbers:
        if _within_tolerance(value, expected, tolerance):
            return

    assert False, (
        f"Expected a number within {tolerance:.1%} of {expected}, "
        f"got {numbers} in {content!r}"
    )


def assert_answer_contains_any(reply: Message, phrases: list[str]) -> None:
    content = (reply.content or "").casefold()
    normalized_content = normalize_numeric_text(content)

    for phrase in phrases:
        if phrase.casefold() in content:
            return
        if normalize_numeric_text(phrase.casefold()) in normalized_content:
            return

    assert False, (
        f"Expected answer to contain one of {phrases!r}, got {reply.content!r}"
    )


def assert_max_turns(messages: list[Message], max_turns: int) -> None:
    turns = sum(1 for message in messages if message.role == Role.ASSISTANT)
    assert turns <= max_turns, f"Expected at most {max_turns} assistant turns, got {turns}"


def assert_expectations(
    reply: Message,
    messages: list[Message],
    expect: dict,
) -> None:
    if "must_call_tools" in expect:
        assert_tools_called(messages, expect["must_call_tools"])
    if "must_not_call_tools" in expect:
        assert_tools_not_called(messages, expect["must_not_call_tools"])
    if "answer_contains" in expect:
        assert_answer_contains(reply, expect["answer_contains"])
    if "answer_contains_any" in expect:
        assert_answer_contains_any(reply, expect["answer_contains_any"])
    if "answer_close_to" in expect:
        assert_answer_close_to(
            reply,
            expect["answer_close_to"],
            tolerance=expect.get("tolerance", 0.01),
        )
    if "max_turns" in expect:
        assert_max_turns(messages, expect["max_turns"])
