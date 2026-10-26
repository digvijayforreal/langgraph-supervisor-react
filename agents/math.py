
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import math_llm
from graph.state import AgentState


# ==========================================
# 1. MATH AGENT PROMPT
# ==========================================

MATH_PROMPT = """
You are a specialized Mathematics AI Agent.

Your responsibilities:
- Solve mathematical problems accurately.
- Verify calculations and reasoning.
- Explain solutions clearly.
- Follow the user's requested format.

Important rules:
- Always provide the final mathematical answer.
- Do not include internal metadata or attempt numbers
  in the final answer.
- Do not claim external calculation tools were used
  unless they were actually used.
- If uncertain, explain the uncertainty.
"""


# ==========================================
# 2. MATH AGENT NODE
# ==========================================

def math_node(state: AgentState) -> dict:

    print("\n========== MATH AGENT STARTED ==========")

    messages = [
        SystemMessage(content=MATH_PROMPT),
        *state["messages"]
    ]

    attempts = state.get("attempts", 0)

    # If Supervisor rejected the previous draft,
    # provide its feedback to the Math Agent.
    if attempts > 0:

        messages.append(
            HumanMessage(
                content=f"""
Your previous draft:
{state.get("draft_answer", "")}

Supervisor feedback:
{state.get("review_feedback", "")}

Correct the previous answer.
Check the calculation carefully.

Return only the revised answer.
Do not include attempt numbers or internal metadata.
"""
            )
        )

    # ==========================================
    # 3. CALL GROQ LLM
    # ==========================================

    response = math_llm.invoke(
        messages,
        config={
            "run_name": "Math_LLM",
            "tags": ["math", "worker"]
        }
    )

    # ==========================================
    # 4. DEBUG MODEL RESPONSE
    # ==========================================

    draft = response.content

    print("\n========== MATH AGENT DEBUG ==========")
    print("Response type:", type(draft))
    print("Response content:", repr(draft))
    print("Token usage:", response.usage_metadata)
    print(
        "Finish reason:",
        response.response_metadata.get("finish_reason")
    )
    print("======================================")

    # Check that the response contains usable text.
    if not isinstance(draft, str):
        raise ValueError(
            "Math Agent returned non-text content."
        )

    draft = draft.strip()

    if not draft:
        raise ValueError(
            "Math Agent returned an empty response. "
            f"Finish reason: "
            f"{response.response_metadata.get('finish_reason')}"
        )

    # ==========================================
    # 5. UPDATE LANGGRAPH STATE
    # ==========================================

    print("[MATH AGENT] Draft length:", len(draft))
    print("[MATH AGENT] Attempt:", attempts + 1)

    return {
        "draft_answer": draft,
        "attempts": attempts + 1,
        "worker_usage": response.usage_metadata or {},
        "execution_path": ["math"]
    }
