import hashlib
import importlib.util
import unittest

from app.m4_pdf import (
    MAX_PDF_BYTES, ParsedPdf, PdfPage, PdfParsingError,
    format_pages_for_llm, parse_pdf, verify_deck_quote, verify_email_quote,
)


class QuoteChecks(unittest.TestCase):
    def setUp(self):
        self.parsed = ParsedPdf("example", 2, [
            PdfPage(1, "Total Round Target\n$12,000,000 USD"),
            PdfPage(2, "Requested Fund Check $3,000,000 USD"),
        ])

    def test_real_quote_with_different_whitespace(self):
        self.assertTrue(verify_deck_quote(self.parsed, 1, "Total Round Target   $12,000,000 USD"))

    def test_invented_amount_is_rejected(self):
        self.assertFalse(verify_deck_quote(self.parsed, 1, "$13,000,000 USD"))

    def test_real_quote_on_wrong_page_is_rejected(self):
        self.assertFalse(verify_deck_quote(self.parsed, 2, "$12,000,000 USD"))

    def test_empty_quote_and_invalid_page_are_rejected(self):
        for page, quote in [(1, "  "), (1, None), (None, "Target"), (0, "Target"),
                            (99, "Target"), (True, "Target")]:
            with self.subTest(page=page, quote=quote):
                self.assertFalse(verify_deck_quote(self.parsed, page, quote))

    def test_case_and_punctuation_are_preserved(self):
        self.assertFalse(verify_deck_quote(self.parsed, 1, "total round target"))
        self.assertFalse(verify_deck_quote(self.parsed, 1, "$12.000.000 USD"))

    def test_email_quote_is_checked_against_email(self):
        self.assertTrue(verify_email_quote("We seek\n$3M.", "We seek $3M."))
        self.assertFalse(verify_email_quote("We seek $3M.", "We seek $4M."))
        self.assertFalse(verify_email_quote("We seek $3M.", ""))

    def test_format_keeps_original_page_numbers(self):
        text = format_pages_for_llm(self.parsed)
        self.assertIn("[PAGE 1]", text)
        self.assertIn("[PAGE 2]", text)


class InputChecks(unittest.TestCase):
    def test_empty_wrong_type_and_large_input(self):
        for data, expected_code in [(b"", "pdf_empty"), ("not bytes", "pdf_invalid_input"),
                                    (b"x" * (MAX_PDF_BYTES + 1), "pdf_too_large")]:
            with self.subTest(code=expected_code):
                with self.assertRaises(PdfParsingError) as error:
                    parse_pdf(data)
                self.assertEqual(error.exception.code, expected_code)


HAS_PYMUPDF = importlib.util.find_spec("pymupdf") is not None


@unittest.skipUnless(HAS_PYMUPDF, "PyMuPDF is missing; PDF reading has NOT been tested.")
class PdfReadingChecks(unittest.TestCase):
    def make_pdf(self, texts, *, user_password=None):
        import pymupdf
        with pymupdf.open() as document:
            for text in texts:
                page = document.new_page()
                if text:
                    page.insert_text((50, 70), text)
            options = {}
            if user_password is not None:
                options = {"encryption": pymupdf.PDF_ENCRYPT_AES_256,
                           "owner_pw": "owner-test-only", "user_pw": user_password}
            return document.tobytes(**options)

    def test_text_pdf_and_hash(self):
        data = self.make_pdf(["A company is raising a twelve million dollar Series A round."])
        parsed = parse_pdf(data)
        self.assertEqual(parsed.page_count, 1)
        self.assertIn("twelve million", parsed.pages[0].text)
        self.assertEqual(parsed.sha256, hashlib.sha256(data).hexdigest())

    def test_blank_middle_page_keeps_numbering(self):
        data = self.make_pdf(["First page contains enough useful company information to extract.", "",
                              "Third page contains enough useful financing information to extract."])
        parsed = parse_pdf(data)
        self.assertEqual([page.page_number for page in parsed.pages], [1, 2, 3])
        self.assertEqual(parsed.pages[1].text, "")
        self.assertTrue(any(w.code == "partial_text_coverage" for w in parsed.warnings))

    def test_no_text_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf([""]))
        self.assertEqual(error.exception.code, "pdf_no_usable_text")

    def test_title_only_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Title"]))
        self.assertEqual(error.exception.code, "pdf_no_usable_text")

    def test_invalid_pdf_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(b"This is not a PDF.")
        self.assertEqual(error.exception.code, "pdf_invalid")

    def test_25_pages_accepted_and_26_rejected(self):
        text = "This page contains useful text about a company and its financing round."
        self.assertEqual(parse_pdf(self.make_pdf([text] * 25)).page_count, 25)
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf([text] * 26))
        self.assertEqual(error.exception.code, "pdf_too_many_pages")

    def test_encrypted_pdf_with_user_password_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Enough useful company text for a normal parsing result."],
                                    user_password="user-test-only"))
        self.assertEqual(error.exception.code, "pdf_encrypted")

    def test_encrypted_pdf_with_empty_user_password_is_rejected(self):
        with self.assertRaises(PdfParsingError) as error:
            parse_pdf(self.make_pdf(["Enough useful company text for a normal parsing result."],
                                    user_password=""))
        self.assertEqual(error.exception.code, "pdf_encrypted")


if __name__ == "__main__":
    unittest.main()
