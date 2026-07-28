from clients.openai_client import OpenAIClient

from schemas.ai_response import DocumentAIResponse


class AIService:

    def __init__(self):
        self.provider = OpenAIClient()


    def analyze_document(self, text):

        response = self.provider.analyze(
            text
        )

        return DocumentAIResponse(
            **response
        )