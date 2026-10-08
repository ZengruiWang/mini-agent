import re

_NUMBER_PATTERN = re.compile(r"-?\d[\d,]*\.?\d*")


def normalize_numeric_text(text: str) -> str:
    return text.replace(",", "").replace(" ", "")


def extract_numbers(text: str) -> list[float]:
    normalized = normalize_numeric_text(text)
    numbers: list[float] = []
    for match in _NUMBER_PATTERN.finditer(normalized):
        token = match.group()
        if token in {"-", ".", "-."}:
            continue
        try:
            numbers.append(float(token))
        except ValueError:
            continue
    return numbers
