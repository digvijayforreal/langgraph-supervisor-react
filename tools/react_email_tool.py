
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (PROJECT_ROOT / "data" / "react_reports").resolve()


@tool
def react_send_email(
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str = "",
) -> str:
    """Send an email directly to the specified recipient.
    Only call this tool when the user explicitly asks to SEND the email.
    Never call it for a draft or when the user says not to send.
    An optional PDF attachment must be inside data/react_reports/.
    """

    recipient = recipient.strip()
    subject = subject.strip()
    body = body.strip()

    if not recipient or "@" not in recipient:
        return "Email not sent: provide a valid recipient address."

    if not subject or not body:
        return "Email not sent: subject and body are required."

    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM")

    if not all([host, port, username, password, sender]):
        return "Email not sent: SMTP configuration is incomplete in .env."

    attachment = None

    if attachment_path.strip():
        try:
            candidate = Path(attachment_path).resolve()
            candidate.relative_to(REPORT_DIR)

            if not candidate.is_file() or candidate.suffix.lower() != ".pdf":
                return "Email not sent: attachment must be an existing PDF report."

            attachment = candidate

        except (ValueError, OSError):
            return (
                "Email not sent: attachments must be PDF files "
                "inside data/react_reports/."
            )

    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = subject
    email.set_content(body)

    if attachment:
        email.add_attachment(
            attachment.read_bytes(),
            maintype="application",
            subtype="pdf",
            filename=attachment.name,
        )

    try:
        with smtplib.SMTP(host, int(port), timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(email)

        return f"Email sent successfully to {recipient}."

    except Exception:
        print("Email delivery failed. Check SMTP configuration and server logs.")
        return (
            "Email delivery failed. Check the server terminal and SMTP settings."
        )
