# context_manager.py
import json
from collections import deque

class ContextManager:
    def __init__(self, max_chars=300000):
        self.context = deque()
        self.max_chars = max_chars
        self.char_count = 0
        self.last_user_instruction = None
        self.saved_contexts = []

    def add_message(self, role, content):
        message = {"role": role, "content": content}
        self.context.append(message)
        self.char_count += len(str(message))

        if role == "user" and content.startswith("aishell command:"):
            self.last_user_instruction = message

        self._prune()

    def add_command(self, input_cmd, stdout, stderr, from_llm=False):
        content = json.dumps({"input": input_cmd, "stdout": stdout, "stderr": stderr})
        self.add_message("user", content if not from_llm else "")
        self.add_message("assistant", content if from_llm else "")
        #self.add_message("user" if not from_llm else "assistant", content)
        #self.add_message("assistant" if not from_llm else "user", "")

    def save_context(self, context):
        self.saved_contexts.append({"role": "user", "content": f"{{\"savedcontext\": \"{context}\"}}"})
        self.saved_contexts.append({"role": "assistant", "content": ""})

    def get_context(self, for_question=False):
        if for_question:
            return list(self.context)[-self.max_chars:]
        
        relevant_context = []
        char_count = 0
        for message in reversed(self.context):
            if message == self.last_user_instruction:
                relevant_context.append(message)
                break
            if char_count + len(str(message)) <= self.max_chars:
                relevant_context.append(message)
                char_count += len(str(message))
            else:
                break
        
        return list(reversed(relevant_context))

    def _prune(self):
        while self.char_count > self.max_chars:
            if len(self.context) > 1 and self.context[0] != self.last_user_instruction and self.context[0] not in self.saved_contexts:
                removed = self.context.popleft()
                self.char_count -= len(str(removed))
            else:
                break

        if self.char_count > self.max_chars:
            truncated_chars = self.char_count - self.max_chars
            self.add_message("user", f"[approximately {truncated_chars} bytes of content has been removed for brevity in this conversation]")