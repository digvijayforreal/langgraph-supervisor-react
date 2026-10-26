
import json
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient


load_dotenv()


@tool
def web_search(query: str) -> str:
    """
    Search the live internet for information.

    Use this tool for current information, recent
    events, documentation, research, and facts.

    Returns source titles, URLs, and excerpts.
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return json.dumps({
            "error": "TAVILY_API_KEY is not configured."
        })

    client = TavilyClient(api_key=api_key)

    try:
        results = client.search(
            query=query,
            search_depth="basic",
            max_results=4,
            include_answer=False,
            include_raw_content=False
        )

        sources = []

        for item in results.get("results", []):
            sources.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:1000]
            })

        return json.dumps({
            "query": query,
            "sources": sources
        }, ensure_ascii=False)

    except Exception as error:
        return json.dumps({
            "error": f"Web search failed: {error}"
        })
