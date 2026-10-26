
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

from langchain_core.messages import (
    AIMessage,
    ToolMessage
)

from agents.document_intelligence import (
    run_document_analysis
)

from tools.document_tools import DOCUMENT_DIR


# ==========================================
# 1. CREATE SAMPLE PDF
# ==========================================

pdf_path = DOCUMENT_DIR / "sample_report.pdf"

doc = SimpleDocTemplate(
    str(pdf_path),
    pagesize=A4,
    title="Orion Project Report"
)

styles = getSampleStyleSheet()

elements = [
    Paragraph(
        "Orion Project Report",
        styles["Title"]
    ),
    Spacer(1, 25),
    Paragraph(
        "Project manager: Mira Shah.",
        styles["Normal"]
    ),
    Spacer(1, 12),
    Paragraph(
        "Project deadline: 15 December 2026.",
        styles["Normal"]
    ),
    Spacer(1, 12),
    Paragraph(
        "Project objective: Develop an AI assistant.",
        styles["Normal"]
    ),

    PageBreak(),

    Paragraph(
        "Orion Project Budget",
        styles["Title"]
    ),
    Spacer(1, 30)
]

table_data = [
    ["Item", "Cost"],
    ["Laptop", "90000"],
    ["Keyboard", "20000"]
]

table = Table(
    table_data,
    colWidths=[200, 130],
    rowHeights=35
)

table.setStyle(
    TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ])
)

elements.append(table)

doc.build(elements)

print("\nSample PDF created:", pdf_path)


# ==========================================
# 2. TEST CASES
# ==========================================

tests = [
    {
        "name": "PDF Reading",
        "query": (
            "Use read_pdf to read sample_report.pdf. "
            "Tell me its title and number of pages."
        ),
        "expected_tool": "read_pdf"
    },
    {
        "name": "Document Search",
        "query": (
            "Use search_document on sample_report.pdf "
            "with query='project deadline'. "
            "Find the deadline and its page number."
        ),
        "expected_tool": "search_document"
    },
    {
        "name": "Table Extraction",
        "query": (
            "Use extract_tables on sample_report.pdf. "
            "List the project budget items and costs."
        ),
        "expected_tool": "extract_tables"
    }
]


# ==========================================
# 3. RUN TESTS
# ==========================================

for test in tests:

    print(
        "\n========== "
        + test["name"]
        + " =========="
    )

    result = run_document_analysis(
        test["query"]
    )

    requested_tools = []

    for message in result["messages"]:

        if isinstance(message, AIMessage):

            for call in message.tool_calls:

                requested_tools.append(
                    call["name"]
                )

                print(
                    "\nTOOL REQUESTED:",
                    call["name"]
                )

                print(
                    "ARGUMENTS:",
                    call["args"]
                )

        if isinstance(message, ToolMessage):

            print(
                "\nTOOL RESULT:",
                str(message.content)[:1800]
            )

    assert requested_tools == [
        test["expected_tool"]
    ], f"Wrong tool: {requested_tools}"

    data = result["tool_results"][0]

    assert data["success"] is True

    assert data["tool"] == test["expected_tool"]

    # PDF reading
    if test["expected_tool"] == "read_pdf":

        assert data["total_pages"] == 2

        assert "Orion" in data["pages"][0]["text"]

    # Search
    elif test["expected_tool"] == "search_document":

        assert data["matches"]

        assert any(
            match["page"] == 1
            and "15 December 2026" in match["passage"]
            for match in data["matches"]
        )

    # Table extraction
    elif test["expected_tool"] == "extract_tables":

        assert data["tables_found"] >= 1

        all_values = " ".join(
            str(cell)
            for table in data["tables"]
            for row in (
                [table["headers"]] + table["rows"]
            )
            for cell in row
        )

        assert "Laptop" in all_values
        assert "90000" in all_values
        assert "Keyboard" in all_values
        assert "20000" in all_values

    print("\nFINAL ANSWER:")
    print(result["answer"])

    print(
        "\nTEST PASSED:",
        test["name"]
    )


print(
    "\n========== "
    "ALL DOCUMENT INTELLIGENCE TESTS PASSED"
    " =========="
)
