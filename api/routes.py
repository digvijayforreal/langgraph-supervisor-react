from time import perf_counter

from fastapi import APIRouter
from langchain_core.messages import HumanMessage

from api.schemas import ChatRequest, ChatResponse
from core.config import MODEL_NAMES
from graph.workflow import app_graph

router = APIRouter(tags=["Chat"])


def initial_graph_state(message: str) -> dict:
    return {
        "messages": [HumanMessage(content=message)],
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
        "tool_events": [],
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    start = perf_counter()
    result = app_graph.invoke(
        initial_graph_state(request.message),
        config={"run_name": "Chat_API", "recursion_limit": 15},
    )
    selected = result["selected_agent"]
    return ChatResponse(
        query=request.message,
        answer=str(result["messages"][-1].content),
        selected_agent=selected,
        model=MODEL_NAMES[selected],
        routing_reason=result["routing_reason"],
        execution_path=result["execution_path"],
        execution_time_ms=round((perf_counter() - start) * 1000, 2),
        approved=result["approved"],
        review_score=result["review_score"] if result["attempts"] else None,
        review_feedback=result["review_feedback"],
        attempts=result["attempts"],
    )
