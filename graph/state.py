from operator import add
from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    selected_agent: Literal["supervisor", "research", "data_analyst", "document"] | None
    routing_reason: str
    phase: Literal["routing", "working", "revision", "complete"]
    draft_answer: str
    approved: bool
    review_score: int
    review_feedback: str
    attempts: int
    supervisor_usage: dict
    worker_usage: dict
    execution_path: Annotated[list[str], add]
    tool_events: Annotated[list[dict], add]
