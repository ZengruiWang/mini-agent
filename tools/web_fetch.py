import re
from typing import Any

from ddgs import DDGS

from tools.base_tool import Tool

_FOOTNOTE_PATTERN = re.compile(r"\n\[\d+\]:")
_DEFAULT_MAX_CHARS = 8000


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

        res = DDGS().extract(url=url)
        return _clean_fetched_content(str(res["content"]), url)
