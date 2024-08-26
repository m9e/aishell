# llm_interface.py

import os
import json
import sys
import re
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
        
        if response is None:
            return None, "Failed to generate a command. There might be an issue with the LLM service."

        # Strip markdown code block if present
        json_match = re.search(r'```(?:json)?\s*({\s*"bash":\s*.*?})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)
        else:
            # If no code block, try to find JSON object directly
            json_match = re.search(r'({.*?"bash".*?})', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

        try:
            command_json = json.loads(response)
            if "bash" in command_json:
                return json.dumps(command_json), None
            else:
                return None, f"Invalid response format from LLM: {response}"
        except json.JSONDecodeError:
            return None, f"Failed to parse LLM response as JSON: {response}"


    def answer_question(self, question, context):
        messages = context + [
            {"role": "user", "content": f"[USERQUESTION] All previous messages were context from an ongoing shell session. The user would like you to answer, in plain text, this question:\n\n{question}"}
        ]

        system_content = LLMPrompts.QUESTION_ANSWERING

        response = self.call_llm(messages, system_content)
        if response is None:
            return "Failed to generate an answer. There might be an issue with the LLM service."
        return response