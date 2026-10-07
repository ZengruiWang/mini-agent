import re
from typing import Any

import trafilatura
from ddgs import DDGS

from tools.base_tool import Tool

_FOOTNOTE_PATTERN = re.compile(r"\n\[\d+\]:")
_DEFAULT_MAX_CHARS = 8000
_EXTRACTION_FAILED = (
    "[No readable content extracted — page may require JavaScript. Try another URL from the search results.]"
)
_LOW_VALUE_RATIO = 0.01
_MIN_USEFUL_CHARS = 800
_LOW_VALUE_NOTICE = (
    "[Low-value extraction: very little text relative to page size. "
    "Page may require JavaScript or be mostly navigation. Try another URL from the search results.]"
)


def _is_low_value_extraction(html: str, text: str) -> bool:
    if text == _EXTRACTION_FAILED or not html:
        return False
    text_len = len(text)
    if text_len >= _MIN_USEFUL_CHARS:
        return False
    return text_len / len(html) < _LOW_VALUE_RATIO


def _extract_text_from_html(html: str, url: str) -> str:
    text = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
    )
    return text.strip() if text else _EXTRACTION_FAILED


def _clean_fetched_content(content: str, url: str, *, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Prepare raw page extract for the LLM. Adjust or bypass here if results are poor."""
    text = str(content).strip()

    match = _FOOTNOTE_PATTERN.search(text)
    if match:
        text = text[: match.start()].strip()

    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[Content truncated.]"

    return f"Fetched from {url}:\n\n{text}"


class WebFetch(Tool):
    name = "web_fetch"
    description = (
        "Fetch and read the full text content of a web page URL. "
        "Required after web_search when snippets do not contain the specific facts needed "
        "(e.g. daily temperatures, prices, scores). "
        "Pass a URL from web_search results. "
        "Do not use for search — use web_search first to find URLs."
    )
    inputs = {
        "url": {
            "type": "string",
            "description": (
                "Full HTTP or HTTPS URL to fetch, e.g. a link from web_search results. "
                "Must start with http:// or https://."
            ),
        }
    }
    output_type = "string"

    def execute(self, **arguments: Any) -> str:
        url = arguments.get("url")
        if not url:
            raise ValueError("web_fetch requires a 'url' argument")
        url = str(url).strip()

        res = DDGS().extract(url=url, fmt="text")
        html = str(res["content"])
        text = _extract_text_from_html(html, url)
        if _is_low_value_extraction(html, text):
            text = f"{_LOW_VALUE_NOTICE}\n\n{text}"
        return _clean_fetched_content(text, url)
