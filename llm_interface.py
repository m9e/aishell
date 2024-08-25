import os
from openai import AzureOpenAI

class LLMInterface:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def generate_command(self, instruction):
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that generates bash commands."},
                    {"role": "user", "content": f"Generate a bash command for: {instruction}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating command: {e}")
            return None

    def answer_question(self, question, context):
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that answers questions based on given context."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error answering question: {e}")
            return None