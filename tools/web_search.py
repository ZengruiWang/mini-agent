from enum import Enum
from typing import Any

from ddgs import DDGS

from tools.base_tool import Tool

class SearchEngine(Enum):
    DUCKDUCKGO = 1

class WebSearch(Tool):

    name = "web_search"
    description = (
        "Search the web for up-to-date information. "
        "Use for current events, weather, news, prices, sports scores, "
        "or any fact that may have changed after your training data. "
        "Returns short snippets and URLs — use web_fetch to read a page in full. "
        "Do not use for pure math — use the calculator tool instead."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": (
                "A concise search query, e.g. 'weather Los Angeles today' "
                "or 'latest news on ...'. Use keywords, not full sentences."
            ),
        }
    }
    output_type = "string"

    def __init__(self, search_engine: SearchEngine | None = None):
        # later if we want to provider multiple search engine
        self.search_engine = search_engine if search_engine else SearchEngine.DUCKDUCKGO

    def execute(self, **arguments: Any) -> str:
        query = arguments.get("query")
        if query is None:
            raise ValueError("web_search requires a 'query' argument")
        query = str(query).strip()
        if not query:
            raise ValueError("web_search query cannot be empty")

        if self.search_engine == SearchEngine.DUCKDUCKGO:
            results = DDGS().text(query, max_results=5)
            if not results:
                return "No results found."
            lines = [f'Search results for "{query}":', ""]
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                body = r.get("body", "")[:300]
                url = r.get("href", "")
                lines.append(f"{i}. **{title}**")
                lines.append(f"   {body}")
                lines.append(f"   {url}")
                lines.append("")
            lines.append(
                "Snippets may be incomplete. Use web_fetch on a URL above for full page content."
            )
            return "\n".join(lines).strip()
        else:
            raise ValueError(f"Unsupported search engine: {self.search_engine}")
