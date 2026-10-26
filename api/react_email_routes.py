
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

router = APIRouter(
    prefix="/api/react/email",
    tags=["ReAct Email Approval"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = (PROJECT_ROOT / "data" / "react_reports").resolve()


class ApprovedEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=20000)
    attachment_filename: Optional[str] = None


@router.post("/send")
def send_approved_email(request: ApprovedEmailRequest):
    """Send an email only when the user explicitly calls this endpoint."""

    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM")

    if not all([host, port, username, password, sender]):
        raise HTTPException(
            status_code=503,
            detail="Email sending is not configured.",
        )

    attachment = None

    if request.attachment_filename:
        filename = request.attachment_filename

        if (
            Path(filename).name != filename
            or "/" in filename
            or "\\" in filename
            or not filename.lower().endswith(".pdf")
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid attachment filename.",
            )

        try:
            attachment = (REPORT_DIR / filename).resolve()
            attachment.relative_to(REPORT_DIR)
        except (ValueError, OSError):
            raise HTTPException(
                status_code=400,
                detail="Invalid attachment path.",
            )

        if not attachment.is_file():
            raise HTTPException(
                status_code=404,
                detail="PDF attachment not found.",
            )

    email = EmailMessage()
    email["From"] = sender
    email["To"] = str(request.recipient)
    email["Subject"] = request.subject
    email.set_content(request.body)

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

    except Exception:
        # Do not expose SMTP credentials or internal server details.
        print("Approved email delivery failed. Check SMTP configuration and logs.")
        raise HTTPException(
            status_code=502,
            detail="Email delivery failed. Check the server terminal.",
        )

    return {
        "status": "sent",
        "message": "Email sent successfully.",
        "recipient": str(request.recipient),
    }
