from pydantic import BaseModel, Field
from typing import Dict


class DocumentAIResponse(BaseModel):

    document_type: str = Field(
        description="Detected document category"
    )

    summary: str = Field(
        description="Short summary of the document"
    )

    entities: Dict[str, str] = Field(
        default_factory=dict,
        description="Extracted key-value entities"
    )

    confidence_score: float = Field(
        ge=0,
        le=1,
        description="AI confidence score between 0 and 1"
    )