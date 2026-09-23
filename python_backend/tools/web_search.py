"""
web_search.py — Free internet search tool using DuckDuckGo.
"""

from langchain_core.tools import tool
from python_backend.tools.security import sanitize_output


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Performs a live web search using DuckDuckGo and returns snippet summaries."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return f"No results found for search query '{query}'."

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"[{i}] {r.get('title')}\nURL: {r.get('href')}\nSnippet: {r.get('body')}\n")
            
            return sanitize_output("\n".join(formatted))
    except Exception as exc:
        return f"Error executing web search: {str(exc)}"
