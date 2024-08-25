from collections import deque

class ContextManager:
    def __init__(self, max_lines=500):
        self.context = deque(maxlen=max_lines)

    def add_line(self, line):
        self.context.append(line)

    def get_context(self):
        return "\n".join(self.context)