from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile, File
from tools.data_tools import UPLOAD_DIR
from tools.document_tools import DOCUMENT_DIR

router = APIRouter(tags=["Uploads"])
MAX_BYTES = 10 * 1024 * 1024

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    original = Path(file.filename or "").name
    suffix = Path(original).suffix.lower()
    if suffix not in {".pdf", ".csv", ".xlsx"}:
        raise HTTPException(400, "Upload a PDF, CSV or XLSX file")
    # Use an opaque server filename, never the client-supplied path.
    stored_name = f"{uuid4().hex[:12]}_{Path(original).stem[:45].replace(' ', '_')}{suffix}"
    target_dir = DOCUMENT_DIR if suffix == ".pdf" else UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / stored_name
    total = 0
    try:
        with target.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(413, "File exceeds 10 MB")
                output.write(chunk)
        if not total:
            raise HTTPException(400, "Empty file")
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return {"file_name": stored_name, "original_name": original,
            "file_type": suffix, "agent": "document" if suffix == ".pdf" else "data_analyst"}
