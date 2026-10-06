# from app.classifiers.factory import create_pitch_classifier
# from fastapi import HTTPException, status, FastAPI
# from app.config import DATA_DIR
# from pathlib import Path
# import base64
# import binascii
# import os
# import logging
# from app.schemas import (
#     EmailEnvelope,
#     TriageResponse,
#     AnalyzeRequest
# )
import asyncio
import logging

from fastapi import FastAPI

from app.classifiers.factory import create_pitch_classifier
from app.config import DATA_DIR
from app.schemas import (
    EmailEnvelope,
    TriageResponse,
    AnalyzeRequest,
    OutcomeRequest,
)
from app.m6_integration import (
    DEMO_LOCK,
    FINAL_STATUSES,
    finish,
    load_record,
    new_record,
    opportunity_id_for,
    require_record,
    require_same_email,
    run_analysis,
    save_record,
    summary,
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

@app.post("/triage", response_model=TriageResponse)
async def triage(email: EmailEnvelope) -> TriageResponse:
    async with DEMO_LOCK:
        opportunity_id = opportunity_id_for(email)
        record = load_record(opportunity_id)

        if record is not None:
            require_same_email(record, email)

            if record["triage"] is not None:
                cached = dict(record["triage"])
                cached.update(
                    record_status=record["status"],
                    reused=True,
                )
                return TriageResponse(**cached)

            finish(
                record,
                "failed",
                "Previous triage was interrupted.",
                "triage_interrupted",
            )

            return TriageResponse(
                status="failed",
                opportunity_id=opportunity_id,
                record_status="failed",
                error_code="triage_interrupted",
                reused=True,
            )

        record = new_record(email)
        save_record(record)

        try:
            result = await asyncio.wait_for(
                classifier.classify(email),
                timeout=120,
            )

            record["classification"] = result.model_dump(
                mode="json"
            )

            action = result.action.value

            record["status"] = (
                "triaged"
                if action == "process"
                else action
            )

            record["reason"] = result.rationale

            response = TriageResponse(
                status="success",
                action=result.action,
                classification=result,
                opportunity_id=opportunity_id,
                record_status=record["status"],
            )

        except Exception as exc:
            code = (
                "classifier_timeout"
                if isinstance(exc, TimeoutError)
                else "classifier_failed"
            )

            logger.error(
                "%s (%s)",
                code,
                type(exc).__name__,
            )

            record.update(
                status="failed",
                reason=code,
                error_code=code,
            )

            response = TriageResponse(
                status="failed",
                error_code=code,
                opportunity_id=opportunity_id,
                record_status="failed",
            )

        record["triage"] = response.model_dump(mode="json")
        save_record(record)

        return response


MAX_PDF_BYTES = 10 * 1024 * 1024
@app.post("/opportunities/{opportunity_id}/analyze")
async def analyze_opportunity(
    opportunity_id: str,
    request: AnalyzeRequest,
):
    async with DEMO_LOCK:
        record = require_record(opportunity_id)
        require_same_email(record, request.email)

        return await run_analysis(record, request)


@app.post("/opportunities/{opportunity_id}/outcome")
async def save_outcome(
    opportunity_id: str,
    request: OutcomeRequest,
):
    async with DEMO_LOCK:
        record = require_record(opportunity_id)

        if (
            record["status"] in FINAL_STATUSES
            or record["status"] == "processing"
        ):
            return summary(record, reused=True)

        return finish(
            record,
            request.status,
            request.reason,
            request.error_code,
        )


@app.get("/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: str):
    return summary(require_record(opportunity_id), reused=True)