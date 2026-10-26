from langchain_core.messages import HumanMessage, SystemMessage

from core.config import coding_llm
from graph.state import AgentState

CODING_PROMPT = """
You are a specialized Coding AI Agent.
Write and debug code; explain programming concepts clearly.
Follow the exact user's requirements and requested response format.
Do not claim to have executed code unless a real tool has executed it.
"""


def coding_node(state: AgentState) -> dict:
    messages = [SystemMessage(content=CODING_PROMPT), *state["messages"]]
    if state["attempts"] > 0:
        messages.append(HumanMessage(content=(
            f"Previous draft:\n{state['draft_answer']}\n\n"
            f"Supervisor feedback:\n{state['review_feedback']}\n\n"
            "Revise your answer based on this feedback, while following the original query."
        )))
    response = coding_llm.invoke(
        messages, config={"run_name": "Coding_LLM", "tags": ["coding", "worker"]}
    )
    return {
        "draft_answer": str(response.content),
        "attempts": state["attempts"] + 1,
        "worker_usage": response.usage_metadata or {},
        "execution_path": ["coding"],
    }
