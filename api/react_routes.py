
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents.react_agent import build_react_agent, run_react_agent


router = APIRouter(
    prefix="/api/react",
    tags=["Gemini ReAct"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (PROJECT_ROOT / "data" / "react_reports").resolve()


class ReactChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)


class ReactChatResponse(BaseModel):
    workflow: str = "react"
    response: str


def content_to_text(content: Any) -> str:
    """Convert message content into readable text."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))

        return "\n".join(part for part in parts if part).strip()

    return str(content) if content is not None else ""


def sse_event(event_type: str, **data: Any) -> str:
    """Format one Server-Sent Event for the frontend."""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat", response_model=ReactChatResponse)
def react_chat(request: ReactChatRequest):
    """Standard non-streaming ReAct endpoint."""
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    try:
        response = run_react_agent(message)

        return ReactChatResponse(
            workflow="react",
            response=response,
        )

    except Exception as error:
        print(f"ReAct chat error: {error}")
        raise HTTPException(
            status_code=500,
            detail="The ReAct workflow failed. Check the server terminal logs.",
        )


@router.post("/chat/stream")
def react_chat_stream(request: ReactChatRequest):
    """Stream tool activity and the final answer to the frontend."""
    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    def generate():
        try:
            agent = build_react_agent()
            seen_tool_calls = set()
            last_ai_text = ""

            yield sse_event(
                "started",
                message="ReAct workflow started",
            )

            for update in agent.stream(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": message,
                        }
                    ]
                },
                stream_mode="updates",
            ):
                for node_name, node_update in update.items():
                    if not isinstance(node_update, dict):
                        continue

                    node_messages = node_update.get("messages", [])

                    if not isinstance(node_messages, list):
                        continue

                    for msg in node_messages:
                        msg_type = getattr(msg, "type", "")
                        tool_calls = getattr(msg, "tool_calls", None) or []

                        # Report requested tool calls.
                        for call in tool_calls:
                            tool_name = call.get("name", "unknown_tool")
                            call_id = call.get("id") or (
                                f"{tool_name}:{len(seen_tool_calls)}"
                            )

                            if call_id in seen_tool_calls:
                                continue

                            seen_tool_calls.add(call_id)

                            yield sse_event(
                                "tool_started",
                                tool=tool_name,
                                tool_call_id=call_id,
                                status="started",
                            )

                        # Report tool results without exposing full output.
                        if msg_type == "tool":
                            tool_name = (
                                getattr(msg, "name", None)
                                or node_name
                            )

                            yield sse_event(
                                "tool_completed",
                                tool=tool_name,
                                tool_call_id=getattr(
                                    msg,
                                    "tool_call_id",
                                    None,
                                ),
                                status="completed",
                                result_preview=content_to_text(
                                    getattr(msg, "content", "")
                                )[:300],
                            )

                        # Save the latest assistant response.
                        if msg_type == "ai" and not tool_calls:
                            text = content_to_text(
                                getattr(msg, "content", "")
                            )

                            if text:
                                last_ai_text = text

            yield sse_event(
                "completed",
                workflow="react",
                response=(
                    last_ai_text
                    or "The workflow finished without a text response."
                ),
            )

        except Exception as error:
            print(f"ReAct streaming error: {error}")

            yield sse_event(
                "error",
                message=(
                    "The ReAct workflow failed. "
                    "Check the server terminal logs."
                ),
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/reports/{filename}")
def download_react_report(filename: str):
    """Serve only PDF reports inside data/react_reports/."""

    # Reject paths and filenames that are not simple PDF filenames.
    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or not filename.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid report filename.",
        )

    try:
        report_path = (REPORT_DIR / filename).resolve()
        report_path.relative_to(REPORT_DIR)
    except (ValueError, OSError):
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        )

    if not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="PDF report not found.",
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_path.name,
    )
