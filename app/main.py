from fastapi import FastAPI

app = FastAPI(
    title="Investment Intake Copilot",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "investment-intake-api",
    }


@app.post("/triage")
async def triage():
    return {
        "status": "stub",
        "message": "Triage endpoint is not implemented yet.",
        "action": "review_manual",
    }


@app.post("/opportunities/{opportunity_id}/analyze")
async def analyze_opportunity(opportunity_id: str):
    return {
        "status": "stub",
        "opportunity_id": opportunity_id,
        "message": "Analysis pipeline is not implemented yet.",
    }