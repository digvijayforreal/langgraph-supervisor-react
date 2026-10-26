
import json
import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

load_dotenv()


@tool
def react_web_search(query: str) -> str:
    """Search the live web for current information, research, incidents,
    official documentation, and recent events. Return source titles,
    URLs, and excerpts for further analysis."""

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return json.dumps({
            "error": "TAVILY_API_KEY is not configured."
        })

    try:
        client = TavilyClient(api_key=api_key)

        results = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=False,
            include_raw_content=False,
        )

        sources = []

        for item in results.get("results", []):
            sources.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", "")[:1500],
            })

        return json.dumps({
            "query": query,
            "sources": sources,
        }, ensure_ascii=False)

    except Exception as error:
        return json.dumps({
            "error": f"Web search failed: {error}"
        })
