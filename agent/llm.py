import aiohttp
import json
import logging
from typing import List, Dict, AsyncGenerator, Union

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, deepseek_key: str, groq_key: str):
        self.deepseek_key = deepseek_key
        self.groq_key = groq_key
        self.deepseek_url = "https://api.deepseek.com/chat/completions"
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model_provider: str = "deepseek",
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[AsyncGenerator[str, None], str]:

        if model_provider == "groq":
            url = self.groq_url
            key = self.groq_key
            model = "llama-3.3-70b-versatile"
        else: # Default deepseek
            url = self.deepseek_url
            key = self.deepseek_key
            model = "deepseek-chat"

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        # If streaming, we must return the generator.
        # If not, we await the response and return the string.
        # But `aiohttp` session context manager closes the session.
        # So for streaming, the session must stay open.
        # I will handle session inside.

        if stream:
            return self._stream_request(url, headers, payload)
        else:
            return await self._sync_request(url, headers, payload)

    async def _stream_request(self, url, headers, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"LLM API Error: {response.status} - {error_text}")
                    yield f"Error: {response.status}"
                    return

                async for line in response.content:
                    line = line.strip()
                    if not line or line == b'data: [DONE]':
                        continue
                    if line.startswith(b'data: '):
                        try:
                            data = json.loads(line[6:])
                            content = data['choices'][0]['delta'].get('content', '')
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def _sync_request(self, url, headers, payload):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"LLM API Error: {response.status} - {error_text}")
                    return f"Error: {response.status} - {error_text}"

                data = await response.json()
                return data['choices'][0]['message']['content']
