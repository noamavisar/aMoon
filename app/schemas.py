from pydantic import BaseModel



class AnalyzeRequest(BaseModel):
    attachment_id: str
    filename: str
    mime_type: str
    content_base64: str