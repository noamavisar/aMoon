from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal


# ============================================================
# Email input models
# ============================================================


class EmailAttachment(BaseModel):
    """
    Metadata about an attachment that arrived with the email.

    At the triage/classification stage we do NOT send the file contents
    to the classifier. We only send attachment metadata such as filename.
    """

    attachment_id: str
    filename: str
    mime_type: str


class EmailEnvelope(BaseModel):
    """
    Normalized email object sent by n8n to POST /triage.

    n8n is responsible for reading Gmail and converting the Gmail-specific
    structure into this application-level contract.
    """

    mailbox_id: str
    message_id: str
    thread_id: str | None = None
    received_at: str

    sender: str
    subject: str = ""
    text_body: str = ""

    attachments: list[EmailAttachment] = Field(default_factory=list)


# ============================================================
# Classification models
# ============================================================


class PitchCategory(str, Enum):
    """
    Categories that the M3 classifier is allowed to return.
    """

    NEW_INVESTMENT_PITCH = "new_investment_pitch"
    PORTFOLIO_UPDATE = "portfolio_update"
    SERVICE_PROVIDER = "service_provider"
    RECRUITING = "recruiting"
    NEWSLETTER = "newsletter"
    OTHER = "other"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(str, Enum):
    """
    Qualitative model confidence.

    This is NOT a calibrated probability.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TriageAction(str, Enum):
    """
    Routing decision made by application code after classification.
    """

    PROCESS = "process"
    SKIP = "skip"
    REVIEW_MANUAL = "review_manual"


class ModelClassification(BaseModel):
    """
    Structured output returned by the LLM itself.

    Important:
    the LLM does NOT decide the final routing action.
    The application code converts this result into process / skip /
    review_manual.
    """

    category: PitchCategory
    confidence: ConfidenceLevel
    rationale: str

    review_needs: list[str] = Field(default_factory=list)


class ClassificationResult(BaseModel):
    """
    Final classification result used by the application.

    This combines the model's classification with the deterministic
    routing decision made in Python.
    """

    category: PitchCategory
    confidence: ConfidenceLevel
    rationale: str

    review_needs: list[str] = Field(default_factory=list)

    action: TriageAction

    # True when the email body was longer than the M3 demo limit
    # and only the first 12,000 characters were sent to the classifier.
    truncated_body: bool = False


class TriageResponse(BaseModel):
    """
    Response returned by POST /triage.

    A successful classification contains the routing action and the
    ClassificationResult.

    A classifier/API failure is represented explicitly as failed and
    must not be treated as a normal non-pitch classification.
    """

    status: Literal["success", "failed"]
    action: TriageAction | None = None
    classification: ClassificationResult | None = None
    error_code: str | None = None





# ============================================================
# PDF analysis request
# ============================================================


class AnalyzeRequest(BaseModel):
    """
    Request sent to the analysis endpoint after triage has decided
    that the email should be processed.

    The PDF itself is transferred as base64 only at the analysis stage,
    not during classification.
    """

    attachment_id: str
    filename: str
    mime_type: str
    content_base64: str