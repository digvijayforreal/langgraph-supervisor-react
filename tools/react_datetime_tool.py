
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import tool


@tool
def react_datetime(
    action: str = "now",
    start_datetime: str = "",
    end_datetime: str = "",
) -> str:
    """Get the current date and time or calculate a time difference.

    Actions:
    - now: return the current Asia/Kolkata date and time.
    - difference: calculate the difference between two ISO-format
      datetime strings, such as 2026-10-25T10:00:00.
    """

    try:
        timezone = ZoneInfo("Asia/Kolkata")

        if action == "now":
            now = datetime.now(timezone)
            return (
                f"Current date: {now.strftime('%Y-%m-%d')}\n"
                f"Current time: {now.strftime('%H:%M:%S')}\n"
                f"Timezone: Asia/Kolkata (IST)"
            )

        if action == "difference":
            if not start_datetime or not end_datetime:
                return (
                    "Error: provide both start_datetime and "
                    "end_datetime in ISO format."
                )

            start = datetime.fromisoformat(start_datetime)
            end = datetime.fromisoformat(end_datetime)

            # Treat naive input datetimes as India local time.
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone)

            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone)

            delta = end - start
            total_seconds = int(delta.total_seconds())
            sign = "-" if total_seconds < 0 else ""
            total_seconds = abs(total_seconds)

            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            return (
                f"Time difference: {sign}{days} days, "
                f"{hours} hours, {minutes} minutes, "
                f"{seconds} seconds."
            )

        return (
            "Unknown action. Use 'now' or 'difference'."
        )

    except Exception as error:
        return f"Date/time operation failed: {error}"
