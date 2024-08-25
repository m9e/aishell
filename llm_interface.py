# llm_interface.py
import os
import json
import sys
from openai import AzureOpenAI
from llm_prompts import LLMPrompts

class LLMInterface:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    def call_llm(self, messages, system_content):
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "system", "content": system_content}] + messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling LLM: {e}", file=sys.stderr)
            return None

    def generate_command(self, instruction, context, interactive_mode, remaining_commands, limit):
        messages = [
            {"role": "user", "content": f"aishell command: {instruction}"}
        ] + context

        system_content = LLMPrompts.COMMAND_GENERATION.format(
            mode="interactive" if interactive_mode else "non-interactive",
            verification="your commands will be verified by the user" if interactive_mode else "your commands will execute without review",
            remaining=remaining_commands,
            limit=limit
        )

        response = self.call_llm(messages, system_content)
        
        if response:
            try:
                command_json = json.loads(response)
                if "bash" in command_json:
                    return command_json["bash"]
            except json.JSONDecodeError:
                pass
        
        return None

    def answer_question(self, question, context):
        messages = context + [
            {"role": "user", "content": f"[USERQUESTION] All previous messages were context from an ongoing shell session. The user would like you to answer, in plain text, this question:\n\n{question}"}
        ]

        system_content = LLMPrompts.QUESTION_ANSWERING

        return self.call_llm(messages, system_content)