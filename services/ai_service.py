import json

from clients.openai_client import (
    OpenAIClient
)



class AIService:


    def __init__(self):

        self.client = OpenAIClient()



    def analyze_document(
        self,
        text
    ):


        prompt = f"""
You are an AI document intelligence system.

Analyze the following document.

Return ONLY JSON.

Required format:

{{
 "document_type": "",
 "summary": "",
 "entities": {{
    "vendor": "",
    "invoice_number": "",
    "invoice_date": "",
    "amount": "",
    "currency": ""
 }},
 "key_points": [],
 "confidence_score": 0.0
}}


Document:

{text}
"""


        result = self.client.analyze(
            prompt
        )


        return json.loads(result)