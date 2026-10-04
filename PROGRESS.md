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