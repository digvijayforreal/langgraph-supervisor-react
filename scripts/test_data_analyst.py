
import json

import pandas as pd

from langchain_core.messages import (
    AIMessage,
    ToolMessage
)

from agents.data_analyst import run_data_analysis
from tools.data_tools import (
    UPLOAD_DIR,
    CHART_DIR
)


# ==========================================
# 1. CREATE SAMPLE DATASET
# ==========================================

dataset_path = UPLOAD_DIR / "sales.csv"

df = pd.DataFrame([
    {"product": "Laptop", "revenue": 50000},
    {"product": "Mouse", "revenue": 10000},
    {"product": "Laptop", "revenue": 40000},
    {"product": "Keyboard", "revenue": 20000},
    {"product": "Mouse", "revenue": 5000}
])

df.to_csv(
    dataset_path,
    index=False
)

print("\nSample dataset created:")
print(dataset_path)
print(df.to_string(index=False))


# ==========================================
# 2. RUN TEST QUERIES
# ==========================================

tests = [
    {
        "name": "Dataset Inspection",
        "query": (
            "Use inspect_dataset to inspect "
            "sales.csv and list its columns."
        ),
        "expected_tool": "inspect_dataset"
    },
    {
        "name": "Revenue Analysis",
        "query": (
            "Use analyze_dataset on sales.csv. "
            "Calculate the sum of revenue grouped "
            "by product. Which product has the "
            "highest total revenue? "
            "The columns are product and revenue."
        ),
        "expected_tool": "analyze_dataset"
    },
    {
        "name": "Chart Generation",
        "query": (
            "Use generate_chart on sales.csv. "
            "Create a bar chart of the sum of "
            "revenue grouped by product. "
            "Use group_by=product and "
            "value_column=revenue."
        ),
        "expected_tool": "generate_chart"
    }
]


for test in tests:

    print(
        "\n========== "
        + test["name"]
        + " =========="
    )

    result = run_data_analysis(
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
                str(message.content)[:1500]
            )

    assert requested_tools == [
        test["expected_tool"]
    ], (
        f"Wrong tool selection: {requested_tools}"
    )

    tool_result = result["tool_results"][0]

    assert tool_result["tool"] == (
        test["expected_tool"]
    )

    if test["expected_tool"] == "inspect_dataset":

        assert tool_result["rows"] == 5
        assert tool_result["columns"] == [
            "product", "revenue"
        ]

    elif test["expected_tool"] == "analyze_dataset":

        totals = {
            row["group"]: row["value"]
            for row in tool_result["results"]
        }

        assert totals == {
            "Laptop": 90000.0,
            "Keyboard": 20000.0,
            "Mouse": 15000.0
        }

    elif test["expected_tool"] == "generate_chart":

        chart_path = (
            CHART_DIR /
            tool_result["chart_file"]
        )

        assert chart_path.is_file()
        assert chart_path.stat().st_size > 0

        print(
            "\nCHART SAVED:",
            chart_path
        )

    print(
        "\nFINAL ANSWER:\n",
        result["answer"]
    )

    print(
        "\nTEST PASSED:",
        test["name"]
    )


print(
    "\n========== ALL DATA ANALYST TESTS PASSED =========="
)
