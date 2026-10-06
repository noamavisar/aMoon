import unittest

from app.m4_pdf import ParsedPdf, PdfPage

from app.m5_analyst import (
    FACT_FIELDS,
    Fact,
    FounderQuestion,
    ScreeningBrief,
    validate_brief,
)


class BriefValidationTests(unittest.TestCase):
    def setUp(self):
        self.parsed = ParsedPdf(
            "test",
            2,
            [
                PdfPage(
                    1,
                    "Total Round Target $12,000,000 USD",
                ),
                PdfPage(
                    2,
                    "Requested Fund Check $3,000,000 USD",
                ),
            ],
        )

        missing = Fact(
            value=None,
            source="unknown",
            page=None,
            quote=None,
        )

        self.brief = ScreeningBrief(
            **{
                name: missing.model_copy()
                for name in FACT_FIELDS
            },
            traction=[],
            market_claims=[],
            regulatory_claims=[],
            positive_signals=[],
            risks=[],
            critical_unknowns=[
                "Pre-money valuation was not provided."
            ],
            founder_questions=[
                FounderQuestion(
                    question=(
                        "What is the proposed "
                        "pre-money valuation?"
                    ),
                    why_it_matters=(
                        "It is needed to assess "
                        "the financing terms."
                    ),
                )
            ],
            contradictions=[],
        )

        self.brief.round_target = Fact(
            value="$12,000,000 USD",
            source="deck",
            page=1,
            quote=(
                "Total Round Target "
                "$12,000,000 USD"
            ),
        )

    def test_valid_fact_and_missing_values_pass(self):
        validate_brief(
            self.brief,
            "",
            self.parsed,
        )

    def test_invented_quote_is_rejected(self):
        self.brief.round_target.quote = (
            "Total Round Target $13,000,000 USD"
        )

        with self.assertRaises(ValueError):
            validate_brief(
                self.brief,
                "",
                self.parsed,
            )

    def test_wrong_value_with_real_quote_is_rejected(self):
        self.brief.round_target.value = (
            "$13,000,000 USD"
        )

        with self.assertRaises(ValueError):
            validate_brief(
                self.brief,
                "",
                self.parsed,
            )

    def test_wrong_page_is_rejected(self):
        self.brief.round_target.page = 2

        with self.assertRaises(ValueError):
            validate_brief(
                self.brief,
                "",
                self.parsed,
            )

    def test_email_fact_uses_email_only(self):
        self.brief.company_name = Fact(
            value="DemoCo",
            source="email",
            page=None,
            quote="DemoCo is raising capital.",
        )

        validate_brief(
            self.brief,
            "DemoCo is raising capital.",
            self.parsed,
        )

        with self.assertRaises(ValueError):
            validate_brief(
                self.brief,
                "An unrelated email.",
                self.parsed,
            )

    def test_unknown_fact_cannot_have_a_value(self):
        self.brief.pre_money = Fact(
            value="$50M",
            source="unknown",
            page=None,
            quote=None,
        )

        with self.assertRaises(ValueError):
            validate_brief(
                self.brief,
                "",
                self.parsed,
            )


if __name__ == "__main__":
    unittest.main()