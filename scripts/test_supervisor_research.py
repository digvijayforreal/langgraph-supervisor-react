
from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

from graph.workflow import app_graph


query = (
    "Find recent updates to LangGraph Python "
    "and provide two relevant source URLs."
)


initial_state = {
    "messages": [HumanMessage(content=query)],
    "selected_agent": None,
    "routing_reason": "",
    "phase": "routing",
    "draft_answer": "",
    "approved": False,
    "review_score": 0,
    "review_feedback": "",
    "attempts": 0,
    "supervisor_usage": {},
    "worker_usage": {},
    "execution_path": [],
}


print("\n========== SUPERVISOR TEST ==========")
print("QUERY:", query)


result = app_graph.invoke(
    initial_state,
    config={
        "run_name": "Supervisor_Research_Test",
        "recursion_limit": 20,
    }
)


print("\n========== EXECUTION DETAILS ==========")

print("Selected agent:", result["selected_agent"])
print("Execution path:", result["execution_path"])
print("Attempts:", result["attempts"])
print("Approved:", result["approved"])
print("Review score:", result["review_score"])
print("Review feedback:", result["review_feedback"])


print("\n========== FINAL ANSWER ==========")

final_message = next(
    (
        message
        for message in reversed(result["messages"])
        if isinstance(message, AIMessage)
    ),
    None
)

if final_message:
    print(final_message.content)
else:
    print("No final AI response found.")


assert result["selected_agent"] == "research", (
    "Supervisor did not select Research Agent."
)

assert "research" in result["execution_path"], (
    "Research Agent did not execute."
)

assert result["attempts"] >= 1, (
    "Research Agent did not generate a draft."
)

assert final_message is not None, (
    "Supervisor did not produce a final response."
)

assert result["phase"] == "complete", (
    "Workflow did not finish."
)

print("\nSUPERVISOR RESEARCH TEST PASSED")
