from fastapi import FastAPI

from app.config import DATA_DIR


app = FastAPI(
    title="Investment Intake Copilot",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "investment-intake-api",
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists(),
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