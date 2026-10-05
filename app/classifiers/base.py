from typing import Protocol

from app.schemas import EmailEnvelope, ClassificationResult


class PitchClassifier(Protocol):
    async def classify(
        self,
        email: EmailEnvelope,
    ) -> ClassificationResult:
        ...