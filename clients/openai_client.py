from django.conf import settings

from openai import OpenAI



class OpenAIClient:


    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )



    def analyze(
        self,
        prompt
    ):


        response = (
            self.client.chat.completions.create(

                model=settings.OPENAI_MODEL,

                temperature=0,

                response_format={
                    "type": "json_object"
                },

                messages=[

                    {
                        "role": "system",
                        "content":
                        "You extract structured information from documents."
                    },

                    {
                        "role": "user",
                        "content": prompt
                    }

                ]
            )
        )


        return (
            response
            .choices[0]
            .message
            .content
        )