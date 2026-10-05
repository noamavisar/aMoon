"""Run from the project root: python -m scripts.inspect_m4_pdf PDF_PATH."""

import argparse
import json
from pathlib import Path

from app.m4_pdf import (
    PdfParsingError, format_pages_for_llm, parse_pdf, verify_deck_quote,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect one PDF for the lean M4 demo.")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--agilerpm", action="store_true", help="Check the supplied AgileRPM fixture.")
    args = parser.parse_args()

    output_dir = Path("work/m4")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "inspection.json"
    text_path = output_dir / "pages.txt"

    try:
        parsed = parse_pdf(args.pdf_path.read_bytes())
    except FileNotFoundError:
        print(f"File not found: {args.pdf_path}")
        return 2
    except ModuleNotFoundError as exc:
        if exc.name != "pymupdf":
            raise
        print("Missing dependency: install PyMuPDF in the Python environment used for this command.")
        return 2
    except PdfParsingError as exc:
        report = {
            "status": "review_manual", "input_file": str(args.pdf_path),
            "error_code": exc.code, "message": exc.message,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        text_path.write_text(f"No extracted text: {exc.code}\n{exc.message}\n", encoding="utf-8")
        print(f"REVIEW MANUAL: {exc.code}")
        print(exc.message)
        print(f"Report: {report_path}")
        return 2

    report = {"status": "parsed", "input_file": str(args.pdf_path), **parsed.to_dict()}
    checks = {}
    if args.agilerpm:
        checks = {
            "21_pages": parsed.page_count == 21,
            "round_target_on_page_9": verify_deck_quote(parsed, 9, "$12,000,000 USD"),
            "fund_check_on_page_9": verify_deck_quote(parsed, 9, "$3,000,000 USD"),
            "invented_amount_rejected": not verify_deck_quote(parsed, 9, "$13,000,000 USD"),
            "wrong_page_rejected": not verify_deck_quote(parsed, 8, "$12,000,000 USD"),
        }
        report["fixture_checks"] = checks

    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    text_path.write_text(format_pages_for_llm(parsed), encoding="utf-8")
    print(f"PARSED: {parsed.page_count} pages")
    print(f"Warnings: {len(parsed.warnings)}")
    print(f"SHA-256: {parsed.sha256}")
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    print(f"Text: {text_path}")
    print(f"Report: {report_path}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
