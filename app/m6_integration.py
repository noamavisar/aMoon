import asyncio
import base64
import binascii
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

from fastapi import HTTPException

from app.config import DATA_DIR

from app.m5_analyst import analyze_email_and_deck, validate_brief
from app.deck_extractor import (
    parse_pptx_document,
    DeckExtractionError,
)


DEMO_LOCK = asyncio.Lock()
FINAL_STATUSES = {"completed", "skip", "review_manual", "failed"}
MAX_DECK_BYTES = 10 * 1024 * 1024

PPTX_MIME = (
    "application/vnd.openxmlformats-officedocument."
    "presentationml.presentation"
)


def is_pptx_attachment(
    filename: str,
    mime_type: str,
) -> bool:
    return (
        mime_type.lower() == PPTX_MIME
        or filename.lower().endswith(".pptx")
    )


def now():
    return datetime.now(timezone.utc).isoformat()


def opportunity_id_for(email):
    message_id = email.message_id

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", message_id):
        raise HTTPException(400, "Invalid message_id")

    return f"m2_{message_id}"


def folder(opportunity_id):
    if not re.fullmatch(r"m2_[A-Za-z0-9_-]{1,128}", opportunity_id):
        raise HTTPException(400, "Invalid opportunity_id")

    return Path(DATA_DIR) / "m2_received" / opportunity_id


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def save_record(record):
    record["updated_at"] = now()

    write_text(
        folder(record["opportunity_id"]) / "record.json",
        json.dumps(record, ensure_ascii=False, indent=2),
    )


def load_record(opportunity_id):
    path = folder(opportunity_id) / "record.json"

    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def require_record(opportunity_id):
    record = load_record(opportunity_id)

    if record is None:
        raise HTTPException(
            404,
            "No saved triage record; run /triage first",
        )

    return record


def require_same_email(record, email):
    if record["email"] != email.model_dump(mode="json"):
        raise HTTPException(
            409,
            "Email differs from the saved triage input",
        )


def new_record(email):
    return {
        "schema_version": 1,
        "opportunity_id": opportunity_id_for(email),
        "email": email.model_dump(mode="json"),
        "triage": None,
        "classification": None,
        "status": "classifying",
        "reason": "classification_started",
        "error_code": None,
        "created_at": now(),
        "updated_at": now(),
        "analyst_runs": 0,
        "deck": None,
        "analysis": None,
        "warnings": [],
        "processing_notes": [],
        "external_verification": "not_performed",
    }


def summary(record, reused=False):
    directory = folder(record["opportunity_id"])

    return {
        "opportunity_id": record["opportunity_id"],
        "status": record["status"],
        "reason": record["reason"],
        "error_code": record["error_code"],
        "analyst_runs": record["analyst_runs"],
        "reused": reused,
        "record_path": str(directory / "record.json"),
        "brief_path": (
            str(directory / "brief.txt")
            if record["status"] == "completed"
            else None
        ),
    }


def finish(record, status, reason, error_code=None):
    record.update(
        status=status,
        reason=reason,
        error_code=error_code,
        finished_at=now(),
    )

    save_record(record)
    return summary(record)


def render_brief(record):
    brief = record["analysis"]["brief"]

    lines = [
        "INVESTMENT INTAKE — INITIAL SCREENING BRIEF",
        f"Opportunity: {record['opportunity_id']}",
        f"Email subject: {record['email']['subject']}",
        "Sources reviewed: email and supplied pitch deck.",
        "External verification: not performed.",
        "Source matching confirms presence, not the truth of company claims.",
        "Prepared for human review. No investment score or automated decision.",
    ]

    def heading(title):
        lines.extend(["", title, "-" * len(title)])

    def fact(label, item):
        if item["value"] is None:
            lines.append(
                f"{label}: Not provided / unresolved if listed below."
            )
            return

        source = (
            f"Deck slide {item['page']}"
            if item["source"] == "deck"
            else "Email body"
        )

        lines.extend([
            f"{label}: {item['value']}",
            f"  Source: {source}",
            f"  Quote: {item['quote']}",
        ])

    heading("COMPANY SNAPSHOT — SOURCE CLAIMS")

    for key, label in [
        ("company_name", "Company"),
        ("product", "Product"),
        ("target_customer", "Target segment claimed"),
    ]:
        fact(label, brief[key])

    heading("DEAL SNAPSHOT — SOURCE CLAIMS")

    for key, label in [
        ("funding_round", "Funding round"),
        ("round_target", "Total round target"),
        ("requested_fund_check", "Amount requested from this fund"),
        ("amount_raised_to_date", "Previous fundraising (scope as quoted)"),
        ("pre_money", "Pre-money valuation"),
        ("use_of_funds", "Use of funds"),
    ]:
        fact(label, brief[key])

    lines.append(
        "A figure described as historical R&D funding does not establish "
        "total capital raised to date."
    )

    heading("REPORTED TRACTION")

    for i, item in enumerate(
        brief["traction"],
        1,
    ):
        fact(
            f"{i}. {item['label']}",
            item,
        )

    if not brief["traction"]:
        lines.append(
            "Not provided in the validated output."
        )

    for key, title in [
        (
            "market_claims",
            "COMPANY MARKET CLAIMS — NOT EXTERNALLY VERIFIED",
        ),
        (
            "regulatory_claims",
            "COMPANY REGULATORY CLAIMS — NOT EXTERNALLY VERIFIED",
        ),
    ]:
        heading(title)

        for i, item in enumerate(
            brief[key],
            1,
        ):
            fact(str(i), item)

        if not brief[key]:
            lines.append(
                "Not provided in the validated output."
            )

    for key, title in [
        (
            "positive_signals",
            "POSITIVE SIGNALS — INITIAL INTERPRETATIONS",
        ),
        ("risks", "RISKS — INITIAL INTERPRETATIONS"),
    ]:
        heading(title)

        for item in brief[key]:
            lines.append(f"- {item['point']}")
            lines.append(
                "  Based on fields: "
                + ", ".join(item["supporting_fields"])
            )

        if not brief[key]:
            lines.append("No supported items returned.")

    heading("CONTRADICTIONS — UNRESOLVED")

    for item in brief["contradictions"]:
        lines.append(item["topic"])
        fact("First claim", item["first"])
        fact("Second claim", item["second"])

    if not brief["contradictions"]:
        lines.append(
            "None reported by this run; this does not prove absence."
        )

    heading("CRITICAL UNKNOWNS")

    lines.extend(
        f"- {item}"
        for item in brief["critical_unknowns"]
    )

    if not brief["critical_unknowns"]:
        lines.append(
            "None returned; this does not establish completeness."
        )

    heading("FOUNDER QUESTIONS")

    for i, item in enumerate(brief["founder_questions"], 1):
        lines.extend([
            f"{i}. {item['question']}",
            f"   Why it matters: {item['why_it_matters']}",
        ])

    heading("EXTRACTION WARNINGS AND PROCESSING NOTES")

    lines.extend(f"- {item}" for item in record["warnings"])
    lines.extend(f"- {item}" for item in record["processing_notes"])

    if not record["warnings"] and not record["processing_notes"]:
        lines.append("None.")

    return "\n".join(lines) + "\n"


async def run_analysis(record, request):
    if record["status"] != "triaged":
        return summary(record, reused=True)

    directory = folder(
        record["opportunity_id"]
    )

    record.update(
        status="processing",
        reason="analysis_started",
        started_at=now(),
    )
    save_record(record)

    try:
        pptx_files = [
            item
            for item in record["email"]["attachments"]
            if is_pptx_attachment(
                item["filename"],
                item["mime_type"],
            )
        ]

        if len(pptx_files) != 1:
            raise DeckProcessingError(
                "deck_count_invalid",
                "Expected exactly one PPTX deck.",
            )

        selected_deck = pptx_files[0]

        if (
            request.attachment_id
            != selected_deck["attachment_id"]
            or request.filename
            != selected_deck["filename"]
        ):
            raise DeckProcessingError(
                "deck_attachment_mismatch",
                "Wrong deck attachment.",
            )

        if not is_pptx_attachment(
            request.filename,
            request.mime_type,
        ):
            raise DeckProcessingError(
                "deck_mime_unsupported",
                "Expected a PPTX deck.",
            )

        max_base64 = 4 * (
            (MAX_DECK_BYTES + 2) // 3
        )

        if (
            len(request.content_base64)
            > max_base64
        ):
            raise DeckProcessingError(
                "deck_too_large",
                "Deck exceeds 10 MiB.",
            )

        try:
            pptx_bytes = base64.b64decode(
                request.content_base64,
                validate=True,
            )
        except (
            binascii.Error,
            ValueError,
        ) as exc:
            raise DeckProcessingError(
                "deck_invalid_base64",
                "Invalid Base64.",
            ) from exc

        if len(pptx_bytes) > MAX_DECK_BYTES:
            raise DeckProcessingError(
                "deck_too_large",
                "Deck exceeds 10 MiB.",
            )

        try:
            parsed = await asyncio.to_thread(
                parse_pptx_document,
                pptx_bytes,
            )
        except DeckExtractionError as exc:
            raise DeckProcessingError(
                "deck_extraction_failed",
                str(exc),
            ) from exc

        write_text(
            directory / "deck.txt",
            parsed.full_text,
        )

        record["deck"] = {
            "attachment_id":
                request.attachment_id,
            "filename":
                request.filename,
            "mime_type":
                request.mime_type,
            "decoded_size_bytes":
                len(pptx_bytes),
            "slide_count":
                parsed.page_count,
            "char_count":
                parsed.char_count,
            "sha256":
                parsed.sha256,
            "text_file":
                "deck.txt",
        }

        record["warnings"] = [
            item.message
            for item in parsed.warnings
        ]

        model = (
            os.getenv("ANALYSIS_MODEL")
            or os.getenv("CLASSIFIER_MODEL")
            or ""
        ).strip()

        if not model:
            return finish(
                record,
                "failed",
                "analysis_model_missing",
                "analysis_model_missing",
            )

        record["analyst_runs"] += 1
        record["analysis_model"] = model
        save_record(record)

        debug_dir = (
            directory / "analysis_debug"
        )

        brief = await analyze_email_and_deck(
            record["email"],
            parsed,
            model,
            output_dir=debug_dir,
        )

        validate_brief(
            brief,
            record["email"]["text_body"],
            parsed,
        )

        notes_path = (
            debug_dir / "cleanup.json"
        )

        notes = json.loads(
            notes_path.read_text(
                encoding="utf-8"
            )
        )["notes"]

        record["processing_notes"] = notes

        record["analysis"] = {
            "model": model,
            "brief": brief.model_dump(
                mode="json"
            ),
        }

        write_text(
            directory / "brief.txt",
            render_brief(record),
        )

        reason = (
            "brief_saved_with_notes"
            if notes or record["warnings"]
            else "brief_saved"
        )

        return finish(
            record,
            "completed",
            reason,
        )

    except DeckProcessingError as exc:
        return finish(
            record,
            "review_manual",
            exc.message,
            exc.code,
        )

    except (ValueError, TypeError) as exc:
        return finish(
            record,
            "review_manual",
            str(exc),
            "analysis_validation_failed",
        )

    except TimeoutError:
        return finish(
            record,
            "failed",
            "Analyst timed out; no automatic retry.",
            "analyst_timeout",
        )

    except OSError:
        return finish(
            record,
            "failed",
            "Could not save the analysis files.",
            "storage_failed",
        )

    except Exception as exc:
        return finish(
            record,
            "failed",
            f"Analyst failed ({type(exc).__name__}).",
            "analyst_failed",
        )

    

class DeckProcessingError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
