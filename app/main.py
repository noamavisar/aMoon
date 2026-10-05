from app.classifiers.factory import create_pitch_classifier
from fastapi import HTTPException, status, FastAPI
from app.config import DATA_DIR
from pathlib import Path
import base64
import binascii
import os
import logging
from app.schemas import (
    EmailEnvelope,
    TriageResponse,
    AnalyzeRequest
)


app = FastAPI(
    title="Investment Intake Copilot",
    version="0.1.0",
)

logger = logging.getLogger(__name__)

classifier = create_pitch_classifier()

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "investment-intake-api",
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists(),
    }

@app.post(
    "/triage",
    response_model=TriageResponse,
)
async def triage(
    email: EmailEnvelope,
) -> TriageResponse:

    try:
        result = await classifier.classify(email)

        return TriageResponse(
            status="success",
            action=result.action,
            classification=result,
            error_code=None,
        )

    except Exception:
        logger.exception("classifier_failed")

        return TriageResponse(
            status="failed",
            action=None,
            classification=None,
            error_code="classifier_failed",
        )
# @app.post("/triage")
# async def triage():
#     return {
#         "status": "stub",
#         "message": "Triage endpoint is not implemented yet.",
#         "action": "process",
#     }


MAX_PDF_BYTES = 10 * 1024 * 1024
@app.post(
    "/opportunities/{opportunity_id}/analyze",
    status_code=status.HTTP_202_ACCEPTED,
)
def analyze_opportunity(
    opportunity_id: str,
    request: AnalyzeRequest,
):
    # 1. Validate MIME type
    if request.mime_type.lower() != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Only application/pdf is supported",
        )

    # 2. Decode Base64 into the original PDF bytes
    try:
        pdf_bytes = base64.b64decode(
            request.content_base64,
            validate=True,
        )
    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid Base64 content",
        )

    # 3. Make sure we actually received data
    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="Decoded PDF is empty",
        )

    # 4. Enforce the M2 limit AFTER decoding
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF exceeds the 10 MiB demo limit",
        )

    # 5. Basic sanity check that the bytes look like a PDF
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Decoded content does not appear to be a PDF",
        )

    # 6. Build a local output directory
    data_root = Path(
        os.getenv("DIR_DATA", "data")
    )

    output_dir = (
        data_root
        / "m2_received"
        / opportunity_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 7. Save the exact bytes received from n8n
    output_path = output_dir / "deck.pdf"

    output_path.write_bytes(pdf_bytes)

    # 8. Return proof that transport worked.
    # Analysis itself is intentionally still a stub in M2.
    return {
        "status": "stub",
        "opportunity_id": opportunity_id,
        "attachment_id": request.attachment_id,
        "filename": request.filename,
        "mime_type": request.mime_type,
        "decoded_size_bytes": len(pdf_bytes),
        "saved_path": str(output_path),
        "message": (
            "PDF received and saved successfully. "
            "Analysis pipeline is not implemented yet."
        ),
    }