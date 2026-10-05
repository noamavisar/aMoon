from app.config import (
    CLASSIFIER_PROVIDER,
    CLASSIFIER_MODEL,
)

from app.classifiers.base import PitchClassifier
from app.classifiers.llm import LlmPitchClassifier


def create_pitch_classifier() -> PitchClassifier:

    provider = CLASSIFIER_PROVIDER.lower()

    if provider == "llm":
        if not CLASSIFIER_MODEL:
            raise ValueError(
                "CLASSIFIER_MODEL is not configured"
            )

        return LlmPitchClassifier(
            model=CLASSIFIER_MODEL,
        )

    raise ValueError(
        f"Unsupported classifier provider: {provider}"
    )