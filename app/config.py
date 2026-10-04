import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLASSIFIER_PROVIDER = os.getenv(
    "CLASSIFIER_PROVIDER",
    "llm",
)

CLASSIFIER_MODEL = os.getenv(
    "CLASSIFIER_MODEL",
    "",
)

MODEL_ANALYSIS = os.getenv(
    "MODEL_ANALYSIS",
    "",
)

DATA_DIR = Path(
    os.getenv("DATA_DIR", "./data")
)