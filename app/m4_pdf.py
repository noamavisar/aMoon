"""Small PDF reader and literal quote checks for the lean M4 demo."""

from dataclasses import asdict, dataclass, field
import hashlib
import re


MAX_PDF_BYTES = 10 * 1024 * 1024 #delete from all instences 
MAX_PDF_PAGES = 25
MIN_USEFUL_PAGE_CHARS = 40


@dataclass
class PdfPage:
    page_number: int
    text: str


@dataclass
class PdfWarning:
    code: str
    page: int | None
    message: str


@dataclass
class ParsedPdf:
    sha256: str
    page_count: int
    pages: list[PdfPage]
    warnings: list[PdfWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class PdfParsingError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(pdf_bytes: bytes) -> ParsedPdf:
    if not isinstance(pdf_bytes, (bytes, bytearray)):
        raise PdfParsingError("pdf_invalid_input", "Expected PDF bytes.")
    if not pdf_bytes:
        raise PdfParsingError("pdf_empty", "The PDF is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise PdfParsingError("pdf_too_large", "The PDF exceeds 10 MiB.")

    # Only PDF reading needs the external package.
    import pymupdf

    try:
        document = pymupdf.open(stream=bytes(pdf_bytes), filetype="pdf")
    except pymupdf.FileDataError as exc:
        raise PdfParsingError("pdf_invalid", "Cannot open this PDF.") from exc

    with document:
        if document.needs_pass:
            raise PdfParsingError("pdf_encrypted", "Encrypted PDFs are unsupported.")
        encryption = (document.metadata or {}).get("encryption")
        if encryption and str(encryption).lower() != "none":
            raise PdfParsingError("pdf_encrypted", "Encrypted PDFs are unsupported.")
        if document.page_count == 0:
            raise PdfParsingError("pdf_no_pages", "The PDF has no pages.")
        if document.page_count > MAX_PDF_PAGES:
            raise PdfParsingError("pdf_too_many_pages", "The PDF exceeds 25 pages.")

        pages = []
        warnings = []
        useful_pages = 0

        for index in range(document.page_count):
            page_number = index + 1
            try:
                text = document[index].get_text("text", sort=True).strip()
            except RuntimeError as exc:
                raise PdfParsingError(
                    "pdf_extraction_failed", f"Cannot read PDF page {page_number}."
                ) from exc

            pages.append(PdfPage(page_number=page_number, text=text))
            normalized = normalize_whitespace(text)
            if not normalized:
                warnings.append(PdfWarning("empty_page", page_number, "No text extracted."))
            elif len(normalized) < MIN_USEFUL_PAGE_CHARS:
                warnings.append(PdfWarning("short_page", page_number, "Very little text extracted."))
            else:
                useful_pages += 1

        if useful_pages == 0:
            raise PdfParsingError(
                "pdf_no_usable_text",
                "No usable text layer found. This demo does not use OCR.",
            )
        if useful_pages < document.page_count:
            warnings.append(PdfWarning(
                "partial_text_coverage", None,
                f"Useful text extracted on {useful_pages} of {document.page_count} pages.",
            ))

        return ParsedPdf(
            sha256=hashlib.sha256(pdf_bytes).hexdigest(),
            page_count=document.page_count,
            pages=pages,
            warnings=warnings,
        )


def format_pages_for_llm(parsed) -> str:
    return "\n\n".join(
        f"[SLIDE {page.page_number}]\n{page.text}"
        for page in parsed.pages
    )


def verify_deck_quote(
    parsed,
    page_number: int | None,
    quote: str | None,
) -> bool:
    if (
        type(page_number) is not int
        or not isinstance(quote, str)
    ):
        return False

    normalized_quote = normalize_whitespace(
        quote
    )

    if not normalized_quote:
        return False

    for page in parsed.pages:
        if page.page_number == page_number:
            return (
                normalized_quote
                in normalize_whitespace(
                    page.text
                )
            )

    return False


def verify_email_quote(email_body: str, quote: str | None) -> bool:
    if not isinstance(quote, str):
        return False
    normalized_quote = normalize_whitespace(quote)
    return bool(normalized_quote) and normalized_quote in normalize_whitespace(email_body)
