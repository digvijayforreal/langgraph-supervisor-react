import json
from dotenv import load_dotenv

from langchain_core.messages import (
    AIMessage,
    ToolMessage
)

from agents.research import run_research


load_dotenv()


query = (
    "Find recent updates to LangGraph Python "
    "and provide two relevant source URLs."
)

print("\n========== RESEARCH TEST ==========")
print("QUERY:", query)

result = run_research(query)

print("\n========== TOOL EXECUTION ==========")

tool_calls = 0

for message in result["messages"]:

    if isinstance(message, AIMessage):
        for call in message.tool_calls:
            tool_calls += 1

            print("\nTOOL REQUESTED:", call["name"])
            print("ARGUMENTS:", call["args"])

    if isinstance(message, ToolMessage):
        print("\nTOOL RESULT:")
        print(str(message.content)[:2000])

print("\nTOTAL TOOL CALLS:", tool_calls)

print("\n========== FINAL ANSWER ==========")
print(result["answer"])

if tool_calls == 0:
    raise AssertionError("LLM did not call a tool.")

if not result["tool_results"]:
    raise AssertionError("No tool results were returned.")

valid_sources = 0

for tool_result in result["tool_results"]:

    data = json.loads(tool_result.content)

    if data.get("error"):
        raise AssertionError(
            f"Web search failed: {data['error']}"
        )

    valid_sources += len(data.get("sources", []))

if valid_sources == 0:
    raise AssertionError(
        "Search completed but returned no sources."
    )

print(f"\nVALID SOURCES: {valid_sources}")
print("\nRESEARCH TOOL TEST PASSED")