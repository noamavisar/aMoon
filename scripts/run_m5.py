import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from app.m4_pdf import parse_pdf
from app.m5_analyst import analyze_email_and_deck


async def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--email",
        default="fixtures/m5/email.json",
    )

    parser.add_argument(
        "--pdf",
        default="fixtures/m4/agilerpm_text_reference.pdf",
    )

    args = parser.parse_args()

    load_dotenv(
        Path(".env"),
        override=False,
    )

    model = (
        os.getenv("ANALYSIS_MODEL")
        or os.getenv("CLASSIFIER_MODEL")
        or ""
    ).strip()

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY is missing from the environment"
        )

    if not model:
        raise ValueError(
            "Set ANALYSIS_MODEL or CLASSIFIER_MODEL"
        )

    output_dir = Path("work/m5")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_path = output_dir / "result.json"

    result_path.write_text(
        json.dumps({"status": "running"}),
        encoding="utf-8",
    )

    try:
        email = json.loads(
            Path(args.email).read_text(
                encoding="utf-8-sig"
            )
        )

        if not isinstance(email, dict):
            raise ValueError(
                "The email fixture must be a JSON object"
            )

        parsed = parse_pdf(
            Path(args.pdf).read_bytes()
        )

        print(
            f"Reading {parsed.page_count} PDF pages. "
            "Calling the analyst..."
        )

        brief = await analyze_email_and_deck(
            email,
            parsed,
            model,
        )

    except Exception as exc:
        result_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "error_type": type(exc).__name__,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        raise

    result = {
        "status": "validated",
        "model": model,
        "pdf_sha256": parsed.sha256,
        "external_verification": "not_performed",
                "processing_notes": json.loads(
            (output_dir / "cleanup.json").read_text(
                encoding="utf-8"
            )
        )["notes"],
        "warnings": [
            warning.message
            for warning in parsed.warnings
        ],
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

    for label, field in [
        ("Company", "company_name"),
        ("Round target", "round_target"),
        ("Requested fund check", "requested_fund_check"),
    ]:
        value = getattr(brief, field).value

        print(
            f"{label}: {value or 'Not provided'}"
        )

    print("Founder questions:")

    for item in brief.founder_questions:
        print(f"- {item.question}")

    print(
        "M5 local run succeeded. "
        "Source quotes validated."
    )

    print(f"Result: {result_path}")


if __name__ == "__main__":
    asyncio.run(main())