import os
import json
import sys
from openai import AzureOpenAI

class LLMInterface:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def is_valid_bash_command(self, response_content: str) -> bool:
        try:
            response_json = json.loads(response_content)
            return isinstance(response_json, dict) and "bash" in response_json and isinstance(response_json["bash"], str)
        except json.JSONDecodeError:
            return False

    def generate_command(self, instruction):
        messages = [
            {"role": "system", "content": "You are an AI assistant that generates bash commands. You are in a terminal, and so you adhere very strictly to formatting requests."},
            {"role": "user", "content": f'Generate a bash command for: {instruction}; output it in the format: {{"bash": "<command>"}}'}
        ]

        retries = 2

        while retries > 0:
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages
                )
                response_content = response.choices[0].message.content.strip()

                # Extract JSON part from the response content
                start_index = response_content.find('{')
                end_index = response_content.rfind('}') + 1
                if start_index != -1 and end_index != -1:
                    json_content = response_content[start_index:end_index]

                    if self.is_valid_bash_command(json_content):
                        return json_content  # Return the JSON string directly
                    else:
                        messages.append({"role": "assistant", "content": response_content})
                        messages.append({"role": "user", "content": 'Your format is invalid and MUST be in the form of {"bash": "<command>"} as valid JSON.'})
                        retries -= 1
                else:
                    messages.append({"role": "assistant", "content": response_content})
                    messages.append({"role": "user", "content": 'Your response does not contain valid JSON. Please provide the command in the format: {"bash": "<command>"}'})
                    retries -= 1
            except Exception as e:
                print(f"Error generating command: {e}", file=sys.stderr)
                return json.dumps({"bash": "echo 'Error generating command'"})

        print("The LLM could not properly respond after multiple attempts.", file=sys.stderr)
        return json.dumps({"bash": "echo 'Failed to generate command'"})

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