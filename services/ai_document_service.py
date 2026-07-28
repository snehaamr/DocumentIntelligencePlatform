from schemas.ai_document_schema import (
    AIDocumentResponse
)

from services.ai_service import AIService



class AIDocumentService:


    def __init__(self):

        self.ai_service = AIService()



    def analyze(
        self,
        extracted_text
    ) -> AIDocumentResponse:


        response = (
            self.ai_service.analyze_document(
                extracted_text
            )
        )


        return AIDocumentResponse(
            **response
        )