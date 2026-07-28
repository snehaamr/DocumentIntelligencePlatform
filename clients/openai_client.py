import json

from openai import OpenAI

from clients.ai_provider import AIProvider


class OpenAIClient(AIProvider):

    def __init__(self):
        self.client = OpenAI()


    def analyze(self, text: str):

        response = self.client.chat.completions.create(

            model=settings.OPENAI_MODEL,

            response_format={
                "type": "json_object"
            },

            messages=[
                {
                    "role": "system",
                    "content": """
You are an AI document intelligence system.

Analyze the document and return JSON:

{
 "document_type": "",
 "summary": "",
 "entities": {},
 "confidence_score": 0.0
}

Rules:
- confidence_score must be between 0 and 1
- extract important entities
- keep summary concise
"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        return json.loads(content)