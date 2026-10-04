from agents import Agent, Runner

from app.config import MODEL_ANALYSIS


if not MODEL_ANALYSIS:
    raise RuntimeError(
        "MODEL_ANALYSIS is not configured in .env"
    )


agent = Agent(
    name="Connection Test",
    instructions="Reply with exactly: API connection OK",
    model=MODEL_ANALYSIS,
)

result = Runner.run_sync(
    agent,
    "Test the API connection.",
)

print(result.final_output)