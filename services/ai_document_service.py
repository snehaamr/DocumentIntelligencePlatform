from services.ai_service import AIService


class AIDocumentService:


    def __init__(self):

        self.ai_service = AIService()



    def analyze(self, text):

        return self.ai_service.analyze_document(
            text
        )