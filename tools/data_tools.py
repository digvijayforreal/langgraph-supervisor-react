
import json
import re
from pathlib import Path
from uuid import uuid4

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from langchain_core.tools import tool


# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

UPLOAD_DIR = ROOT / "data" / "uploads"
CHART_DIR = ROOT / "data" / "charts"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ROWS = 100_000


# ==========================================
# 2. HELPERS
# ==========================================

def get_dataset_path(file_name: str) -> Path:

    if not isinstance(file_name, str):
        raise ValueError("Invalid file name")

    # Accept filename only, not arbitrary paths.
    if (
        file_name != Path(file_name).name
        or "/" in file_name
        or "\\" in file_name
    ):
        raise ValueError("Only filenames are allowed")

    path = (UPLOAD_DIR / file_name).resolve()

    if path.parent != UPLOAD_DIR.resolve():
        raise ValueError("Invalid dataset path")

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV and XLSX are supported")

    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {file_name}"
        )

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("Dataset exceeds 10 MB limit")

    return path


def load_dataframe(file_name: str) -> pd.DataFrame:

    path = get_dataset_path(file_name)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, nrows=MAX_ROWS + 1)
    else:
        df = pd.read_excel(
            path,
            engine="openpyxl",
            nrows=MAX_ROWS + 1
        )

    if len(df) > MAX_ROWS:
        raise ValueError("Dataset exceeds row limit")

    if df.empty:
        raise ValueError("Dataset is empty")

    # Avoid exposing excessively long strings.
    return df


def json_result(data):
    return json.dumps(
        data,
        default=str,
        ensure_ascii=False
    )


def error_result(error):
    return json_result({
        "success": False,
        "error": str(error)
    })


def grouped_values(
    df: pd.DataFrame,
    group_by: str,
    value_column: str,
    operation: str
):

    if group_by not in df.columns:
        raise ValueError(
            f"Unknown group column: {group_by}"
        )

    if value_column not in df.columns:
        raise ValueError(
            f"Unknown value column: {value_column}"
        )

    if operation == "count":
        series = df.groupby(
            group_by,
            dropna=False
        ).size()
    else:
        values = pd.to_numeric(
            df[value_column],
            errors="coerce"
        )

        if values.notna().sum() == 0:
            raise ValueError(
                f"{value_column} has no numeric values"
            )

        prepared = df.assign(
            __numeric_value=values
        )

        series = prepared.groupby(
            group_by,
            dropna=False
        )["__numeric_value"].agg(operation)

    series = series.sort_values(
        ascending=False
    ).head(30)

    return [
        {
            "group": str(index),
            "value": (
                None if pd.isna(value)
                else float(value)
            )
        }
        for index, value in series.items()
    ]


# ==========================================
# 3. TOOL: INSPECT DATASET
# ==========================================

@tool
def inspect_dataset(file_name: str) -> str:
    """
    Inspect a CSV or XLSX dataset.

    Returns columns, data types, row count,
    missing values, and sample records.

    file_name must be a filename inside
    the data/uploads folder.
    """

    try:
        df = load_dataframe(file_name)

        return json_result({
            "success": True,
            "tool": "inspect_dataset",
            "file_name": file_name,
            "rows": len(df),
            "columns": list(df.columns),
            "data_types": {
                col: str(dtype)
                for col, dtype in df.dtypes.items()
            },
            "missing_values": {
                str(col): int(count)
                for col, count
                in df.isna().sum().items()
            },
            "sample_rows": json.loads(
                df.head(5).to_json(
                    orient="records",
                    date_format="iso"
                )
            )
        })

    except Exception as error:
        return error_result(error)


# ==========================================
# 4. TOOL: ANALYZE DATASET
# ==========================================

@tool
def analyze_dataset(
    file_name: str,
    operation: str,
    value_column: str,
    group_by: str = ""
) -> str:
    """
    Analyze numeric values from a dataset.

    operation must be one of:
    sum, mean, min, max, count.

    value_column is the numeric column
    to analyze, except for count.

    group_by is optional. When specified,
    computes the operation for each group.
    """

    try:
        allowed = {
            "sum", "mean", "min", "max", "count"
        }

        if operation not in allowed:
            raise ValueError(
                f"Invalid operation: {operation}"
            )

        df = load_dataframe(file_name)

        if group_by:
            results = grouped_values(
                df,
                group_by,
                value_column,
                operation
            )

            return json_result({
                "success": True,
                "tool": "analyze_dataset",
                "file_name": file_name,
                "operation": operation,
                "value_column": value_column,
                "group_by": group_by,
                "results": results
            })

        if operation == "count":
            answer = int(len(df))
        else:
            if value_column not in df.columns:
                raise ValueError(
                    f"Unknown column: {value_column}"
                )

            values = pd.to_numeric(
                df[value_column],
                errors="coerce"
            )

            if values.notna().sum() == 0:
                raise ValueError(
                    "Column has no numeric values"
                )

            answer = float(
                getattr(values, operation)()
            )

        return json_result({
            "success": True,
            "tool": "analyze_dataset",
            "file_name": file_name,
            "operation": operation,
            "value_column": value_column,
            "group_by": None,
            "result": answer
        })

    except Exception as error:
        return error_result(error)


# ==========================================
# 5. TOOL: GENERATE CHART
# ==========================================

@tool
def generate_chart(
    file_name: str,
    group_by: str,
    value_column: str,
    operation: str = "sum"
) -> str:
    """
    Generate a bar chart from a dataset.

    Groups records by group_by, calculates
    the operation on value_column, and
    saves a PNG chart.

    operation must be sum, mean, min,
    max, or count.
    """

    try:
        if operation not in {
            "sum", "mean", "min", "max", "count"
        }:
            raise ValueError("Invalid operation")

        df = load_dataframe(file_name)

        results = grouped_values(
            df,
            group_by,
            value_column,
            operation
        )

        if not results:
            raise ValueError(
                "No data available for chart"
            )

        labels = [
            row["group"]
            for row in results
        ]

        values = [
            row["value"]
            for row in results
        ]

        fig, ax = plt.subplots(
            figsize=(9, 5)
        )

        ax.bar(labels, values)

        ax.set_title(
            f"{operation.title()} of "
            f"{value_column} by {group_by}"
        )

        ax.set_xlabel(group_by)
        ax.set_ylabel(
            f"{operation}({value_column})"
        )

        plt.xticks(
            rotation=30,
            ha="right"
        )

        fig.tight_layout()

        chart_name = (
            f"chart_{uuid4().hex[:12]}.png"
        )

        chart_path = CHART_DIR / chart_name

        fig.savefig(
            chart_path,
            dpi=140
        )

        plt.close(fig)

        return json_result({
            "success": True,
            "tool": "generate_chart",
            "chart_file": chart_name,
            "chart_path": str(chart_path),
            "results": results
        })

    except Exception as error:
        return error_result(error)
