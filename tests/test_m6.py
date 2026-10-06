import asyncio
import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, patch

from app import main, m6_integration as m6
from app.m4_pdf import parse_pdf
from app.m5_analyst import (
    FACT_FIELDS,
    Fact,
    FounderQuestion,
    ScreeningBrief,
)
from app.m5_cleanup import prepare_brief
from app.schemas import (
    AnalyzeRequest,
    ClassificationResult,
    EmailEnvelope,
    OutcomeRequest,
)


class M6Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.data_patch = patch.object(
            m6,
            "DATA_DIR",
            Path(self.tmp.name),
        )
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)

        self.email = EmailEnvelope(
            mailbox_id="demo",
            message_id="test_m6",
            received_at="2026-10-06",
            sender="founder@example.com",
            subject="Series A pitch",
            text_body=(
                "Acme is raising $12M and requesting "
                "$3M from your fund."
            ),
            attachments=[{
                "attachment_id": "test_m6:attachment_0",
                "filename": "deck.pdf",
                "mime_type": "application/pdf",
            }],
        )

        self.classifier = AsyncMock(
            return_value=ClassificationResult(
                category="new_investment_pitch",
                confidence="high",
                rationale="Explicit fundraising pitch.",
                action="process",
            )
        )

        classifier_patch = patch.object(
            main.classifier,
            "classify",
            self.classifier,
        )
        classifier_patch.start()
        self.addCleanup(classifier_patch.stop)

    def pdf_bytes(self, with_text=True):
        import pymupdf

        with pymupdf.open() as document:
            page = document.new_page()

            if with_text:
                page.insert_text(
                    (72, 72),
                    "Acme provides clinic software. "
                    "This is a text-layer demo PDF.",
                )

            return document.tobytes()

    def request(self, with_text=True):
        return AnalyzeRequest(
            attachment_id="test_m6:attachment_0",
            filename="deck.pdf",
            mime_type="application/pdf",
            email=self.email,
            content_base64=base64.b64encode(
                self.pdf_bytes(with_text)
            ).decode("ascii"),
        )

    def brief(self):
        missing = Fact(
            value=None,
            source="unknown",
            page=None,
            quote=None,
        )

        return ScreeningBrief(
            **{
                name: missing.model_copy()
                for name in FACT_FIELDS
            },
            traction=[],
            market_claims=[],
            regulatory_claims=[],
            positive_signals=[],
            risks=[],
            critical_unknowns=["Valuation not provided."],
            founder_questions=[FounderQuestion(
                question="What is the pre-money valuation?",
                why_it_matters="Financing terms are missing.",
            )],
            contradictions=[],
        )

    async def test_complete_duplicate_and_email_reaches_analyst(self):
        async def fake_analyst(email, parsed, model, output_dir):
            self.assertEqual(
                email["text_body"],
                self.email.text_body,
            )

            output_dir.mkdir(parents=True, exist_ok=True)

            (output_dir / "cleanup.json").write_text(
                '{"notes": []}',
                encoding="utf-8",
            )

            return self.brief()

        analyst = AsyncMock(side_effect=fake_analyst)

        with patch.object(
            m6,
            "analyze_email_and_deck",
            analyst,
        ):
            triage = await main.triage(self.email)
            request = self.request()

            first, second = await asyncio.gather(
                main.analyze_opportunity(
                    triage.opportunity_id,
                    request,
                ),
                main.analyze_opportunity(
                    triage.opportunity_id,
                    request,
                ),
            )

            cached_triage = await main.triage(self.email)

        self.assertEqual(first["status"], "completed")
        self.assertTrue(second["reused"])
        self.assertTrue(cached_triage.reused)
        self.assertEqual(analyst.await_count, 1)
        self.assertEqual(self.classifier.await_count, 1)

        record = m6.require_record(triage.opportunity_id)

        self.assertEqual(record["analyst_runs"], 1)
        self.assertNotIn("content_base64", json.dumps(record))

        report = Path(first["brief_path"]).read_text(
            encoding="utf-8"
        )
        self.assertIn("Not provided", report)

    async def test_pdf_without_text_stops_before_analyst(self):
        triage = await main.triage(self.email)

        with patch.object(
            m6,
            "analyze_email_and_deck",
            AsyncMock(),
        ) as analyst:
            result = await main.analyze_opportunity(
                triage.opportunity_id,
                self.request(False),
            )

        self.assertEqual(result["status"], "review_manual")
        self.assertEqual(
            result["error_code"],
            "pdf_no_usable_text",
        )
        self.assertEqual(analyst.await_count, 0)

    async def test_model_failure_is_saved_and_not_retried(self):
        triage = await main.triage(self.email)
        request = self.request()

        with patch.object(
            m6,
            "analyze_email_and_deck",
            AsyncMock(side_effect=RuntimeError("test")),
        ) as analyst:
            result = await main.analyze_opportunity(
                triage.opportunity_id,
                request,
            )

            repeated = await main.analyze_opportunity(
                triage.opportunity_id,
                request,
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], "analyst_failed")
        self.assertTrue(repeated["reused"])
        self.assertEqual(analyst.await_count, 1)

    async def test_missing_company_name_stays_unknown(self):
        cleaned, notes = prepare_brief(
            self.brief(),
            self.email.model_dump(),
            parse_pdf(self.pdf_bytes()),
        )

        self.assertIsNone(cleaned.company_name.value)
        self.assertTrue(
            any("company_name" in item for item in notes)
        )

    async def test_manual_outcome_is_saved(self):
        triage = await main.triage(self.email)

        result = await main.save_outcome(
            triage.opportunity_id,
            OutcomeRequest(
                status="review_manual",
                reason="expected_exactly_one_pdf_found_0",
            ),
        )

        self.assertEqual(result["status"], "review_manual")
        self.assertEqual(result["analyst_runs"], 0)

    async def test_skip_and_manual_triage_are_persisted(self):
        for action, category in [
            ("skip", "newsletter"),
            ("review_manual", "uncertain"),
        ]:
            email = self.email.model_copy(
                update={"message_id": f"test_{action}"}
            )

            self.classifier.return_value = ClassificationResult(
                category=category,
                confidence="high",
                rationale="Test route.",
                action=action,
            )

            response = await main.triage(email)
            record = m6.require_record(response.opportunity_id)

            self.assertEqual(record["status"], action)
            self.assertEqual(record["analyst_runs"], 0)

    async def test_classifier_failure_does_not_become_skip(self):
        self.classifier.side_effect = RuntimeError("test")

        response = await main.triage(self.email)

        self.assertEqual(response.status, "failed")
        self.assertIsNone(response.action)
        self.assertEqual(
            m6.require_record(response.opportunity_id)["status"],
            "failed",
        )


if __name__ == "__main__":
    unittest.main()