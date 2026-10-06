# PROGRESS

## Current milestone
M1 — Local server and development environment

## Status
Completed

## Completed
- Created Python 3.12 virtual environment
- Installed project dependencies
- Saved working versions to requirements.txt
- Created FastAPI application
- Added GET /health
- Added stub POST /triage
- Added stub POST /opportunities/{id}/analyze
- Added .env and .env.example
- Added .gitignore
- Created Dockerfile
- Created compose.yaml
- Added persistent n8n volume
- Added bind mount for data/
- Verified OpenAI API connectivity
- Verified /health from host
- Verified /health from n8n HTTP Request

## Verification commands

```bash
pytest
docker compose up --build

## Host:
http://localhost:8000/health


## n8n HTTP Request:
GET http://api:8000/health

Blockers
  None
Time spent:
  2.5 Hours

  
Next milestone
M2 — Gmail intake with real OAuth



## M2 — Gmail intake with real OAuth

Status: COMPLETE

Completed:
- Connected self-hosted n8n to Gmail using Custom OAuth2.
- Gmail Trigger polls the pitches-demo label.
- Full Gmail message is fetched by Gmail message ID.
- Plain-text email body is extracted with HTML fallback.
- PDF attachments are downloaded directly by the Gmail node using Download Attachments.
- EmailEnvelope is sent to POST /triage.
- Switch routes process / skip / review_manual.
- process requires exactly one PDF.
- PDF is carried as n8n binary data.
- Binary PDF is converted to standard Base64 using getBinaryDataBuffer().
- PDF payload is sent to POST /opportunities/{id}/analyze.
- API decodes the Base64 and receives the original PDF bytes.
- Live Gmail end-to-end execution completed.

Implementation decisions:
- No separate Gmail attachments.get HTTP request is needed because the installed Gmail node downloads attachments directly into n8n binary data.
- Gmail attachmentId is not exposed by this direct-download path.
- For M2 transport, attachment_id is an internal deterministic identifier:
  <message_id>:<binary_property>.
- M2 uses a temporary opportunity ID of m2_<message_id>.
  Final opportunity ID generation will be implemented in M7.
- /triage is still a development stub.
  Real classification is M3.

Validation:
- Live Gmail message received.
- message_id present.
- thread_id present.
- sender present.
- subject present.
- full text_body present.
- one PDF detected.
- PDF MIME type = application/pdf.
- n8n decoded PDF byte size: XXXXXXX.
- API decoded PDF byte size: XXXXXXX.
- Sizes match.
- Received PDF opens successfully.
- Workflow exported without secrets or private pinned data.

Time spent:
  4 Hours

Next milestone:
M3 — modular LLM classifier



## M3 — Modular LLM classifier

Status: complete

Implemented:
- PitchClassifier protocol
- LlmPitchClassifier
- Pydantic structured classification output
- deterministic action routing
- classifier provider factory
- /triage connected to the real classifier
- 12,000 character body limit and truncated_body flag
- explicit failed state for classifier errors

Tests:
python -m pytest tests/test_classifier.py -v

Live scenarios:
- clear pitch -> process
- newsletter/service provider -> skip
- ambiguous introduction -> review_manual

Blockers:
None

Next:
M4 — PDF extraction and evidence validation


Time spent:
  2.5 Hours



  ## M4 — Lean PDF Parsing and Quote Validation

Status: completed locally

### Implemented
- Added `app/m4_pdf.py` for PDF text extraction and quote validation.
- Added `scripts/inspect_m4_pdf.py` for local PDF inspection.
- Added `tests/test_m4_pdf.py` with 16 automated tests.
- Preserved PDF page numbering, including empty pages.
- Added extraction warnings and explicit rejection of unsupported PDFs.
- Added literal quote checks for PDF pages and email text.

### Verification
- All 16 tests passed with no skipped tests.
- Positive fixture: `fixtures/m4/agilerpm_text_reference.pdf`.
- Extracted 21 pages.
- Confirmed the $12,000,000 round target and $3,000,000 requested fund check on page 9.
- Rejected an invented amount and a quote attributed to the wrong page.
- Manually compared pages 1 and 9 against the PDF.
- Negative fixture: `fixtures/m4/agilerpm_image_only.pdf`.
- Negative fixture stopped with `pdf_no_usable_text`.

### Scope and Limitations
- The positive fixture is a text transcript of the source slides, not a layout-preserving export.
- Quote matching confirms presence in the source, not the truth of company claims.
- OCR and interpretation of charts or images are outside the demo scope.
- API and n8n integration of the parser remain pending.
- The investment brief is not implemented yet.

### Environment
- Python version: 3.12
- PyMuPDF version: 1.28.2
- Positive fixture SHA-256: [value from the successful inspection]
- Known blockers: None

Time spent:
  30 Minutes

  
### Next Milestone
M5 — implement one LLM analyst that receives the email body and
page-numbered deck text, returns a structured screening brief,
and preserves sources, missing information and contradictions.

## M5 — Lean Investment Screening Analyst

Status: completed locally

### Implemented
- Added `app/m5_analyst.py`.
- Added `scripts/run_m5.py`.
- Added `tests/test_m5.py`.
- Implemented one analyst receiving the email body and
  page-numbered PDF text from M4.
- Added a structured ScreeningBrief.
- Added deterministic checks for source quotes and literal values.
- Preserved missing information and source contradictions.

### Verification
- All 6 validation tests passed.
- A live model run produced a validated local brief.
- Manually checked 3 central facts against their sources.
- Kept round target, requested fund check and historical
  fundraising separate.
- Checked that missing pre-money valuation was not inferred.
- Reviewed one risk and one founder question.
- Tested conflicting fund-check amounts:
  $4M in the email versus $3M in the deck.
- Confirmed that both claims and the unresolved conflict
  were preserved.

### Scope
- Sources are the supplied email and PDF only.
- External verification was not performed.
- Quote validation does not establish the truth of company claims.
- Local results are stored under `work/m5`.
- API/n8n integration and final brief storage remain pending.

### Run Details
- Model: gpt-6-luna
- Actual time spent: 45 minutes
- Known blockers: None

### Next
Connect the validated analyst to the existing analyze endpoint,
preserve the email context, and generate the readable text brief.





## M6 — Lean Gmail-to-Brief Integration

Status: completed

### Implemented
- Connected the existing analyze endpoint to M4 PDF extraction
  and one M5 investment screening analyst.
- Preserved text_body and review_manual.
- Preserved the m2_<message_id> opportunity identifier.
- Saved the full email envelope and classification during triage.
- Added email context to the n8n analysis request.
- Added deterministic English brief.txt rendering.
- Saved record.json and brief.txt under:
  data/m2_received/<opportunity_id>/
- Kept source quotes, PDF page numbers, missing information,
  contradictions, extraction warnings and processing notes.
- Added atomic record writes and basic duplicate protection.
- Closed skip, review_manual, attachment-failure and fallback routes.
- Removed the sendAndWait dependency from the lean demo path.

### Verification
- M4, M5 and M6 automated tests passed: 29 tests.
- Live Gmail pitch with one text-layer PDF produced a saved brief.
- Opened brief.txt from the host computer.
- Manually checked central facts against the email and PDF.
- Confirmed separate round target and requested fund check.
- Confirmed missing pre-money valuation remained missing.
- Repeated the same analysis request without another analyst run.
- Newsletter and ambiguous introduction left saved outcomes.
- Missing PDF, multiple PDFs and image-only PDF stopped clearly.
- Conflicting fund-check amounts were retained with both sources.
- Workflow fallback produced an explicit saved failure.

### Decisions and Limitations
- Analysis is synchronous and returns HTTP 200 with an explicit status.
- The previous HTTP 202 endpoint was a transport stub,
  not an implemented background analysis job.
- The API runs as one process for this demo.
- There is no durable queue or automatic recovery/retry after failure.
- Sources are the supplied email and PDF only.
- External verification is not performed.
- Source matching does not establish the truth of company claims.
- The demo produces material for human review,
  without an investment score or automated rejection.
- OCR, runtime PPTX support, web research, multiple specialists,
  an additional synthesizer and a dashboard remain out of scope.

### Run Details
- Actual time spent: 1:20 hour
- Known blockers: None

