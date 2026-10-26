
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from tools.react_web_search import react_web_search
from tools.react_pdf_tool import react_generate_pdf
from tools.react_datetime_tool import react_datetime
from tools.react_email_tool import react_send_email


load_dotenv()


SYSTEM_PROMPT = """
You are a helpful Gemini ReAct assistant with four tools.

IMPORTANT TOOL RULES:

1. EMAIL REQUESTS
- If the user explicitly asks you to SEND an email, collect the
  recipient, subject, and body, then call react_send_email.
- If the user asks for a draft, preview, or says "do not send",
  never call react_send_email. Show the proposed draft as text instead.
- Never claim an email was sent unless the tool confirms success.
- If the recipient, subject, or body is missing, ask for the missing
  information before sending.
  
2. OTHER TOOLS
Use react_web_search for web searches.
Use react_generate_pdf when the user requests a PDF report.
Use react_datetime for date or time questions when appropriate.

3. GENERAL
Answer clearly and accurately.
Use tools when they are relevant.
Never claim a tool was used if you did not call it.
"""


def build_react_agent():
    """Create the Gemini ReAct agent with its four available tools."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Check your project's .env file."
        )

    model = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=api_key,
        temperature=0,
        max_retries=1,
    )

    tools = [
        react_web_search,
        react_generate_pdf,
        react_datetime,
        react_send_email,
    ]

    return create_react_agent(
        model,
        tools,
        prompt=SYSTEM_PROMPT,
    )


def content_to_text(content) -> str:
    """Convert model or tool output into readable text."""

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


def run_react_agent(message: str) -> str:
    """Run the ReAct agent and return its final answer."""

    message = message.strip()

    if not message:
        raise ValueError("Message cannot be empty.")

    agent = build_react_agent()

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": message,
                }
            ]
        }
    )

    messages = result.get("messages", [])

    # Return the actual email tool output so the frontend can recognize
    # the EMAIL PREVIEW format instead of receiving a paraphrased answer.
    for msg in reversed(messages):
        if (
            getattr(msg, "type", "") == "tool"
            and getattr(msg, "name", "") == "react_send_email"
        ):
            return content_to_text(getattr(msg, "content", ""))

    # For all other requests, return the final assistant response.
    for msg in reversed(messages):
        if getattr(msg, "type", "") == "ai":
            if getattr(msg, "tool_calls", None):
                continue

            answer = content_to_text(getattr(msg, "content", ""))

            if answer:
                return answer

    return "The agent finished without producing a text response."
