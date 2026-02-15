import pytest
import asyncio
from agent.core import Agent
from agent.memory import ConversationMemory
from agent.llm import LLMClient
from unittest.mock import MagicMock, AsyncMock

# Mock LLM Client
class MockLLM(LLMClient):
    def __init__(self):
        # Pass dummy keys
        super().__init__("key", "key")
        self.responses = []

    def add_response(self, text):
        self.responses.append(text)

    async def chat_completion(self, messages, stream=False, model_provider="deepseek", temperature=0.7):
        # Returns an async generator, but wrapped in a coroutine
        # because the original method is async def and returns a generator.

        async def generator():
            if not self.responses:
                yield "No response"
                return
            response = self.responses.pop(0)
            # Yield chunks to simulate stream
            # We can just yield the whole string as one chunk for simplicity
            yield response

        return generator()

@pytest.mark.asyncio
async def test_agent_simple_flow():
    llm = MockLLM()
    memory = ConversationMemory()
    agent = Agent(llm) # Removed memory from init

    llm.add_response("Hello user!")

    # Run
    await agent.process("Hi", memory=memory) # Added memory to process

    msgs = memory.get_messages()
    # 1. User
    # 2. Assistant
    assert len(msgs) == 2
    assert msgs[0]["content"] == "Hi"
    assert msgs[1]["content"] == "Hello user!"

@pytest.mark.asyncio
async def test_agent_tool_use():
    llm = MockLLM()
    memory = ConversationMemory()
    agent = Agent(llm) # Removed memory from init

    # Register dummy tool
    async def dummy_tool(arg):
        return f"Result: {arg}"

    agent.register_tool("dummy", dummy_tool, "A dummy tool")

    # 1. LLM calls tool
    llm.add_response('Thinking...\n```json\n{"tool": "dummy", "args": {"arg": "test"}}\n```')
    # 2. LLM gets result and responds final
    llm.add_response("Final answer.")

    await agent.process("Do dummy test", memory=memory) # Added memory to process

    msgs = memory.get_messages()
    # 1. User
    # 2. Assistant (Tool Call)
    # 3. System (Tool Result)
    # 4. Assistant (Final)
    assert len(msgs) == 4
    assert msgs[2]["role"] == "system"
    assert "Result: test" in msgs[2]["content"]
    assert msgs[3]["content"] == "Final answer."
