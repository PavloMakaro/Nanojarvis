from typing import List, Dict

class ConversationMemory:
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        # Keep system prompt if it's the first one? Usually system prompt is prepended dynamically.
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)

    def clear(self):
        self.messages = []
