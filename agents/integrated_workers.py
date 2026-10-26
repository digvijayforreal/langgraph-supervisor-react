"""Adapters for tested standalone tool-enabled worker graphs.
Do NOT replace agents/research.py, agents/data_analyst.py, or agents/document_intelligence.py.
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agents.research import run_research
from agents.data_analyst import run_data_analysis
from agents.document_intelligence import run_document_analysis


def adapt(state, worker_name, runner):
    attempts = state.get("attempts", 0)
    user_text = next((str(m.content) for m in state["messages"] if isinstance(m, HumanMessage)), "")
    if not user_text:
        raise ValueError("Missing user message")
    query = user_text
    if attempts:
        # Retain original filename even for revisions, and provide review context.
        query += ("\n\nSupervisor requested revision. Previous draft:\n" +
                  state.get("draft_answer", "") + "\nReview feedback:\n" +
                  state.get("review_feedback", "") +
                  "\nRun the appropriate tool again and improve the answer, preserving source evidence.")
    result = runner(query)
    events = []
    for msg in result.get("messages", []):
        if isinstance(msg, AIMessage):
            for call in msg.tool_calls:
                events.append({"node": worker_name, "stage": "requested", "name": call["name"],
                               "args": call.get("args", {}), "attempt": attempts + 1})
        elif isinstance(msg, ToolMessage):
            events.append({"node": worker_name, "stage": "result", "name": msg.name or "tool",
                           "result": str(msg.content)[:5000], "attempt": attempts + 1})
    return {"draft_answer": result["answer"], "attempts": attempts + 1,
            "execution_path": [worker_name], "tool_events": events,
            "worker_usage": {}}


def research_node(state):
    return adapt(state, "research", run_research)


def data_analyst_node(state):
    return adapt(state, "data_analyst", run_data_analysis)


def document_node(state):
    return adapt(state, "document", run_document_analysis)
