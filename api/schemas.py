from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=50000)


class ChatResponse(BaseModel):
    query: str
    answer: str
    selected_agent: str
    model: str
    routing_reason: str
    execution_path: list[str]
    execution_time_ms: float
    approved: bool
    review_score: int | None = None
    review_feedback: str = ""
    attempts: int
