
import json
from time import perf_counter

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from api.schemas import ChatRequest
from graph.workflow import app_graph


# ==========================================
# 1. ROUTER CONFIGURATION
# ==========================================

router = APIRouter(tags=["Live Pipeline"])

MAX_ATTEMPTS = 3


# ==========================================
# 2. SERVER-SENT EVENT FORMATTER
# ==========================================

def send_event(event_type, data):

    payload = {
        "type": event_type,
        **data
    }

    return (
        f"data: {json.dumps(payload, default=str)}\n\n"
    )


# ==========================================
# 3. LIVE STREAMING ENDPOINT
# ==========================================

@router.post("/chat/stream")
def stream_chat(request: ChatRequest):

    def generate_events():

        start_time = perf_counter()

        selected_agent = None
        approved = False
        attempts = 0
        score = None
        feedback = ""
        execution_path = []

        # Initial LangGraph State
        initial_state = {
            "messages": [
                HumanMessage(content=request.message)
            ],
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
            "tool_events": []
        }

        # Query received by FastAPI
        yield send_event(
            "query_received",
            {
                "query": request.message
            }
        )

        yield send_event(
            "supervisor_started",
            {
                "node": "supervisor",
                "phase": "routing"
            }
        )

        try:

            # ==================================
            # 4. EXECUTE LANGGRAPH
            # ==================================

            for update in app_graph.stream(
                initial_state,
                stream_mode="updates",
                config={
                    "run_name": "Single_Supervisor_Workflow",
                    "tags": [
                        "langgraph",
                        "single-supervisor"
                    ]
                }
            ):

                # ==================================
                # SUPERVISOR NODE
                # ==================================

                if "supervisor" in update:

                    data = update["supervisor"]

                    # Important:
                    # A LangGraph update contains only
                    # fields returned by that execution.
                    phase = data.get("phase")

                    execution_path.extend(
                        data.get("execution_path", [])
                    )

                    # ----------------------------------
                    # FIRST VISIT: ROUTING OR GENERAL
                    # ----------------------------------

                    if "selected_agent" in data:

                        selected_agent = data["selected_agent"]

                        yield send_event(
                            "supervisor_completed",
                            {
                                "node": "supervisor",
                                "phase": phase,
                                "selected_agent": selected_agent,
                                "routing_reason": data.get(
                                    "routing_reason", ""
                                ),
                                "supervisor_usage": data.get(
                                    "supervisor_usage", {}
                                ),
                                "execution_path": execution_path.copy()
                            }
                        )

                        # Supervisor directly answered
                        # a general knowledge question.
                        if (
                            selected_agent == "supervisor"
                            and phase == "complete"
                        ):

                            approved = True

                            final_answer = str(
                                data["messages"][-1].content
                            )

                            yield send_event(
                                "worker_completed",
                                {
                                    "node": "supervisor",
                                    "answer": final_answer,
                                    "approved": True,
                                    "attempts": 0,
                                    "execution_path": execution_path.copy()
                                }
                            )

                        # Supervisor selected specialist
                        else:

                            yield send_event(
                                "worker_scheduled",
                                {
                                    "node": selected_agent,
                                    "attempt": 1
                                }
                            )

                    # ----------------------------------
                    # RETURN VISIT: ANSWER REVIEW
                    # ----------------------------------

                    elif phase in ("revision", "complete"):

                        approved = data["approved"]
                        score = data["review_score"]
                        feedback = data["review_feedback"]

                        yield send_event(
                            "supervisor_review_completed",
                            {
                                "node": "supervisor",
                                "phase": phase,
                                "approved": approved,
                                "score": score,
                                "feedback": feedback,
                                "attempt": attempts,
                                "supervisor_usage": data.get(
                                    "supervisor_usage", {}
                                ),
                                "execution_path": execution_path.copy()
                            }
                        )

                        # Review rejected:
                        # send task back to same worker.
                        if phase == "revision":

                            yield send_event(
                                "revision_requested",
                                {
                                    "node": selected_agent,
                                    "attempt": attempts + 1,
                                    "feedback": feedback
                                }
                            )

                            yield send_event(
                                "worker_scheduled",
                                {
                                    "node": selected_agent,
                                    "attempt": attempts + 1
                                }
                            )

                        # Review finished:
                        # answer approved or attempt limit.
                        elif phase == "complete":

                            final_answer = str(
                                data["messages"][-1].content
                            )

                            yield send_event(
                                "worker_completed",
                                {
                                    "node": selected_agent,
                                    "answer": final_answer,
                                    "approved": approved,
                                    "review_score": score,
                                    "review_feedback": feedback,
                                    "attempts": attempts,
                                    "execution_path": execution_path.copy()
                                }
                            )

                    else:
                        raise ValueError(
                            f"Unexpected Supervisor update: {data}"
                        )

                # ==================================
                # SELECTED WORKER NODE
                # ==================================

                elif (
                    selected_agent in (
                        "research",
                        "data_analyst",
                        "document"
                    )
                    and selected_agent in update
                ):

                    data = update[selected_agent]

                    attempts = data["attempts"]

                    execution_path.extend(
                        data.get("execution_path", [])
                    )

                    # Internal tool execution has completed; expose evidence to the UI.
                    for tool_event in data.get("tool_events", []):
                        yield send_event("tool_event", tool_event)

                    yield send_event(
                        "worker_draft",
                        {
                            "node": selected_agent,
                            "attempt": attempts,
                            "draft_answer": data[
                                "draft_answer"
                            ],
                            "worker_usage": data.get(
                                "worker_usage", {}
                            ),
                            "execution_path": execution_path.copy()
                        }
                    )

                    # Same Supervisor will review.
                    # No separate Reviewer node.
                    yield send_event(
                        "supervisor_started",
                        {
                            "node": "supervisor",
                            "phase": "review",
                            "attempt": attempts
                        }
                    )

            # ==================================
            # 5. GRAPH EXECUTION COMPLETED
            # ==================================

            total_time = round(
                (perf_counter() - start_time) * 1000,
                2
            )

            yield send_event(
                "completed",
                {
                    "selected_agent": selected_agent,
                    "approved": approved,
                    "attempts": attempts,
                    "execution_path": execution_path.copy(),
                    "execution_time_ms": total_time
                }
            )

        # ==================================
        # 6. ERROR HANDLING
        # ==================================

        except Exception as error:

            yield send_event(
                "error",
                {
                    "message": str(error)
                }
            )

    # ==========================================
    # 7. RETURN STREAMING RESPONSE
    # ==========================================

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
