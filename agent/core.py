import logging
import json
import asyncio
import inspect
from typing import List, Callable, Dict, Any, Union
from .llm import LLMClient
from .memory import ConversationMemory

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, llm: LLMClient, memory: ConversationMemory):
        self.llm = llm
        self.memory = memory
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.system_prompt = (
            "You are GarvisClaw, an intelligent AI agent designed to assist users. "
            "You are running on a constrained environment (100MB RAM), so be efficient. "
            "You have access to the following tools:\n"
            "{tools_desc}\n\n"
            "You may receive system context like '[System Context: chat_id=12345]'. "
            "Use this information when tools require it (e.g., add_reminder needs chat_id). "
            "If the user's request is simple, answer directly. "
            "If it requires tools, use them. "
            "To use a tool, respond with a JSON block: "
            "```json\n"
            "{{\"tool\": \"tool_name\", \"args\": {{...}}}}\n"
            "```\n"
            "If no tool is needed, just respond normally."
        )

    def register_tool(self, name: str, func: Callable, description: str):
        self.tools[name] = {"func": func, "description": description}
        logger.info(f"Registered tool: {name}")

    def _get_tools_desc(self) -> str:
        desc = []
        for name, tool in self.tools.items():
            desc.append(f"- {name}: {tool['description']}")
        return "\n".join(desc)

    async def process(self, user_input: str, update_callback: Callable[[str, bool], Any] = None):
        """
        Process user input.
        update_callback(text, is_status)
        """
        if update_callback:
            await update_callback("Thinking...", True)

        self.memory.add_message("user", user_input)

        step = 0
        max_steps = 5

        while step < max_steps:
            messages = [{"role": "system", "content": self.system_prompt.format(tools_desc=self._get_tools_desc())}]
            messages.extend(self.memory.get_messages())

            # Call LLM
            response_text = ""
            gen = await self.llm.chat_completion(messages, stream=True)

            # Stream response
            async for chunk in gen:
                response_text += chunk
                # Only update if it's the final response or if we are planning
                # If we are inside a tool loop, maybe update differently?
                # For now, just stream everything.
                if update_callback and len(response_text) % 20 == 0:
                    await update_callback(response_text, False)

            if update_callback:
                await update_callback(response_text, False)

            # Check for tool call
            tool_call = self._parse_tool_call(response_text)

            if tool_call:
                tool_name = tool_call.get("tool")
                args = tool_call.get("args", {})

                if tool_name in self.tools:
                    if update_callback:
                        await update_callback(f"Executing {tool_name}...", True)

                    try:
                        func = self.tools[tool_name]["func"]
                        if inspect.iscoroutinefunction(func):
                            result = await func(**args)
                        else:
                            result = await asyncio.to_thread(func, **args)
                        tool_output = f"Tool '{tool_name}' output: {result}"
                    except Exception as e:
                        tool_output = f"Tool '{tool_name}' failed: {str(e)}"

                    # Feed back to LLM
                    self.memory.add_message("assistant", response_text)
                    self.memory.add_message("system", tool_output)
                    step += 1

                    if update_callback:
                        await update_callback("Analyzing result...", True)

                    continue # Loop again
                else:
                    self.memory.add_message("assistant", response_text)
                    break
            else:
                self.memory.add_message("assistant", response_text)
                break

    def _parse_tool_call(self, text: str) -> Union[Dict, None]:
        # Look for ```json ... ``` or just {...}
        try:
            start = text.find("```json")
            if start != -1:
                end = text.find("```", start + 7)
                if end != -1:
                    json_str = text[start+7:end].strip()
                    return json.loads(json_str)
            # Try finding standalone JSON object
            # This is fragile, but sufficient for simple tool use
            pass
        except Exception:
            pass
        return None
