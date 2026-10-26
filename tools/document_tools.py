
import json
import re
from pathlib import Path

from pypdf import PdfReader
import pdfplumber

from langchain_core.tools import tool


# ==========================================
# 1. CONFIGURATION
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

DOCUMENT_DIR = ROOT / "data" / "documents"
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 15 * 1024 * 1024
MAX_PAGES = 100


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def json_result(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        default=str
    )


def error_result(error):
    return json_result({
        "success": False,
        "error": str(error)
    })


def get_pdf_path(file_name: str) -> Path:

    if not isinstance(file_name, str):
        raise ValueError("Invalid filename")

    if (
        not file_name
        or file_name != Path(file_name).name
        or "/" in file_name
        or "\\" in file_name
        or file_name in (".", "..")
    ):
        raise ValueError(
            "Only PDF filenames are allowed"
        )

    path = (DOCUMENT_DIR / file_name).resolve()

    if path.parent != DOCUMENT_DIR.resolve():
        raise ValueError("Invalid document path")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    if not path.is_file():
        raise FileNotFoundError(
            f"Document not found: {file_name}"
        )

    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("PDF exceeds 15 MB limit")

    return path


def load_reader(file_name: str):

    path = get_pdf_path(file_name)
    reader = PdfReader(str(path))

    if reader.is_encrypted:
        raise ValueError(
            "Password-protected PDFs are not supported"
        )

    if len(reader.pages) > MAX_PAGES:
        raise ValueError("PDF exceeds 100-page limit")

    return reader


# ==========================================
# 3. READ PDF TOOL
# ==========================================

@tool
def read_pdf(file_name: str) -> str:
    """
    Read a PDF document and extract text,
    metadata, and page count.

    The PDF must exist inside data/documents.
    """

    try:

        reader = load_reader(file_name)

        pages = []

        for index, page in enumerate(reader.pages):

            if index >= 10:
                break

            text = page.extract_text() or ""

            pages.append({
                "page": index + 1,
                "text": text[:2500]
            })

        metadata = reader.metadata

        title = (
            str(metadata.title)
            if metadata and metadata.title
            else ""
        )

        return json_result({
            "success": True,
            "tool": "read_pdf",
            "file_name": file_name,
            "total_pages": len(reader.pages),
            "title": title,
            "pages": pages,
            "note": (
                "Returns up to 10 pages and "
                "2500 characters per page."
            )
        })

    except Exception as error:
        return error_result(error)


# ==========================================
# 4. SEARCH DOCUMENT TOOL
# ==========================================

@tool
def search_document(
    file_name: str,
    query: str
) -> str:
    """
    Search the text of a PDF using keywords.

    Returns relevant passages with page numbers.
    This performs keyword retrieval, not
    semantic vector retrieval.
    """

    try:

        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "Search query cannot be empty"
            )

        reader = load_reader(file_name)

        stopwords = {
            "the", "is", "are", "was", "were",
            "who", "what", "when", "where",
            "which", "does", "about", "with",
            "from", "this", "that", "and",
            "for", "into", "tell", "me",
            "document", "please", "find"
        }

        terms = {
            word
            for word in re.findall(
                r"\w+", query.lower()
            )
            if len(word) > 2
            and word not in stopwords
        }

        if not terms:
            raise ValueError(
                "No useful search terms provided"
            )

        matches = []

        for page_index, page in enumerate(
            reader.pages
        ):

            text = page.extract_text() or ""

            chunk_size = 850
            overlap = 150
            step = chunk_size - overlap

            for start in range(0, len(text), step):

                passage = text[
                    start:start + chunk_size
                ]

                passage_lower = passage.lower()

                score = sum(
                    len(
                        re.findall(
                            rf"\b{re.escape(term)}\b",
                            passage_lower
                        )
                    )
                    for term in terms
                )

                if score > 0:

                    matches.append({
                        "page": page_index + 1,
                        "score": score,
                        "passage": passage.strip()
                    })

        matches.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return json_result({
            "success": True,
            "tool": "search_document",
            "file_name": file_name,
            "query": query,
            "search_type": "keyword",
            "total_matches": len(matches),
            "matches": matches[:5]
        })

    except Exception as error:
        return error_result(error)


# ==========================================
# 5. EXTRACT TABLES TOOL
# ==========================================

@tool
def extract_tables(file_name: str) -> str:
    """
    Extract tables from a PDF using pdfplumber.

    Returns page numbers, headers, and rows.
    Works best with digitally generated PDFs.
    """

    try:

        path = get_pdf_path(file_name)

        # Validate PDF before processing tables.
        load_reader(file_name)

        extracted = []

        with pdfplumber.open(str(path)) as pdf:

            for page_number, page in enumerate(
                pdf.pages,
                start=1
            ):

                tables = page.extract_tables()

                for index, table in enumerate(tables):

                    if not table:
                        continue

                    extracted.append({
                        "page": page_number,
                        "table_number": index + 1,
                        "headers": table[0],
                        "rows": table[1:101],
                        "total_rows": len(table)
                    })

                    if len(extracted) >= 20:
                        break

                if len(extracted) >= 20:
                    break

        return json_result({
            "success": True,
            "tool": "extract_tables",
            "file_name": file_name,
            "tables_found": len(extracted),
            "tables": extracted
        })

    except Exception as error:
        return error_result(error)
