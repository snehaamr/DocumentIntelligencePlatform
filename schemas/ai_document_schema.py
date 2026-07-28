from pydantic import BaseModel, Field
from typing import Dict, List


class DocumentEntity(BaseModel):

    vendor: str | None = None

    invoice_number: str | None = None

    invoice_date: str | None = None

    amount: str | None = None

    currency: str | None = None



class AIDocumentResponse(BaseModel):

    document_type: str = Field(
        description="Type of document"
    )

    summary: str

    entities: DocumentEntity

    key_points: List[str]

    confidence_score: float