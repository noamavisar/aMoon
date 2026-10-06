import json
from pathlib import Path

from app.m4_pdf import ParsedPdf, PdfPage, PdfWarning
from app.m5_analyst import ScreeningBrief, validate_brief
from app.m5_cleanup import prepare_brief


def main():
    folder = Path("work/m5")
    folder.mkdir(parents=True, exist_ok=True)

    result_path = folder / "result.json"

    result_path.write_text(
        json.dumps({"status": "running"}),
        encoding="utf-8",
    )

    try:
        raw = json.loads(
            (folder / "raw_response.json").read_text(
                encoding="utf-8"
            )
        )

        data = raw["parsed"]

        parsed = ParsedPdf(
            sha256=data["sha256"],
            page_count=data["page_count"],
            pages=[
                PdfPage(**page)
                for page in data["pages"]
            ],
            warnings=[
                PdfWarning(**warning)
                for warning in data["warnings"]
            ],
        )

        brief, notes = prepare_brief(
            ScreeningBrief.model_validate(raw["brief"]),
            raw["email"],
            parsed,
        )

        validate_brief(
            brief,
            raw["email"].get("text_body", ""),
            parsed,
        )

        result = {
            "status": "validated",
            "model": raw["model"],
            "pdf_sha256": parsed.sha256,
            "external_verification": "not_performed",
            "replayed_from_saved_sources": True,
            "warnings": [
                warning.message
                for warning in parsed.warnings
            ],
            "processing_notes": notes,
            "brief": brief.model_dump(mode="json"),
        }

        result_path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    except Exception as exc:
        result_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        raise

    print(f"Company: {brief.company_name.value}")
    print(f"Result: {result_path}")
    print("No model call was made.")


if __name__ == "__main__":
    main()