import re

from app.m4_pdf import normalize_whitespace
from app.m5_analyst import (
    FACT_FIELDS,
    FACT_LISTS,
    Fact,
    FounderQuestion,
)


def prepare_brief(brief, email, parsed):
    # Work on a copy so the original model response remains available.
    brief = brief.model_copy(deep=True)
    notes = []

    sources = [
        (
            "email",
            None,
            normalize_whitespace(email.get("text_body", "")),
        )
    ]

    sources += [
        (
            "deck",
            page.page_number,
            normalize_whitespace(page.text),
        )
        for page in parsed.pages
    ]

    def missing():
        return Fact(
            value=None,
            source="unknown",
            page=None,
            quote=None,
        )

    def clean(fact, label):
        # A missing value must not carry evidence.
        if not fact.value or not fact.value.strip():
            if (
                fact.source,
                fact.page,
                fact.quote,
            ) != ("unknown", None, None):
                notes.append(
                    f"{label}: cleared evidence from a missing value."
                )

            return missing()

        quote = normalize_whitespace(fact.quote or "")

        matches = [
            source
            for source in sources
            if quote and quote in source[2]
        ]

        declared = [
            source
            for source in matches
            if source[:2] == (fact.source, fact.page)
        ]

        if declared:
            source, page, _ = declared[0]

        elif len(matches) == 1:
            source, page, _ = matches[0]
            notes.append(
                f"{label}: corrected source location "
                "using its exact quote."
            )

        else:
            notes.append(
                f"{label}: EXCLUDED; missing or "
                "unverified source quote."
            )
            return missing()

        value = normalize_whitespace(fact.value)

        # Preserve the real source claim instead of an unsupported
        # paraphrase, reformatted amount, or incorrect model value.
        if value not in quote:
            value = quote
            notes.append(
                f"{label}: replaced the model value "
                "with the verified quote."
            )

        return Fact(
            value=value,
            source=source,
            page=page,
            quote=quote,
        )

    # Prefer the company name explicitly supplied with the demo input.
    hint = email.get("company_name")
    candidate = (
        hint
        if hint is not None
        else brief.company_name.value
    )

    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError(
            "Provide company_name in the email input for this demo."
        )

    candidate = normalize_whitespace(candidate)

    pattern = re.compile(
        r"(?<!\w)" + re.escape(candidate) + r"(?!\w)",
        re.I,
    )

    company = None

    for source, page, text in sources:
        match = pattern.search(text)

        if match:
            company = Fact(
                value=match.group(),
                source=source,
                page=page,
                quote=match.group(),
            )
            break

    if company is None:
        raise ValueError(
            "company_name must actually appear "
            "in the email body or PDF text."
        )

    brief.company_name = company

    # Normalize every scalar field, not just the field that failed.
    for name in FACT_FIELDS:
        if name != "company_name":
            setattr(
                brief,
                name,
                clean(getattr(brief, name), name),
            )

    # Remove unsupported list entries and keep the demo concise.
    for name in FACT_LISTS:
        values = [
            clean(fact, f"{name}[{i}]")
            for i, fact in enumerate(getattr(brief, name))
        ]

        values = [
            fact
            for fact in values
            if fact.value is not None
        ]

        if len(values) > 3:
            notes.append(
                f"{name}: limited to 3 source claims."
            )

        setattr(brief, name, values[:3])

    # Never silently discard a reported contradiction.
    for i, conflict in enumerate(brief.contradictions):
        conflict.first = clean(
            conflict.first,
            f"contradictions[{i}].first",
        )

        conflict.second = clean(
            conflict.second,
            f"contradictions[{i}].second",
        )

        if (
            conflict.first.value is None
            or conflict.second.value is None
        ):
            raise ValueError(
                "Unverified contradiction: inspect "
                "raw_response.json before proceeding."
            )

    available = {
        name
        for name in FACT_FIELDS
        if getattr(brief, name).value is not None
    }

    available |= {
        name
        for name in FACT_LISTS
        if getattr(brief, name)
    }

    # Remove conclusions that depend on discarded information.
    for name in ("positive_signals", "risks"):
        original = getattr(brief, name)

        kept = [
            item
            for item in original
            if item.point.strip()
            and item.supporting_fields
            and all(
                field in available
                for field in item.supporting_fields
            )
        ]

        if len(kept) != len(original):
            notes.append(
                f"{name}: removed conclusions "
                "with missing supporting fields."
            )

        if len(kept) > 3:
            notes.append(
                f"{name}: limited to 3 conclusions."
            )

        setattr(brief, name, kept[:3])

    brief.critical_unknowns = list(
        dict.fromkeys(
            [
                note
                for note in notes
                if "EXCLUDED" in note
            ]
            + [
                item
                for item in brief.critical_unknowns
                if item.strip()
            ]
        )
    )[:5]

    brief.founder_questions = [
        item
        for item in brief.founder_questions
        if item.question.strip()
        and item.why_it_matters.strip()
    ][:5]

    if not brief.founder_questions:
        brief.founder_questions = [
            FounderQuestion(
                question=(
                    "Can you provide the missing information "
                    "and supporting documents?"
                ),
                why_it_matters=(
                    "The initial screening contains "
                    "information gaps."
                ),
            )
        ]

    return brief, notes