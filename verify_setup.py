import asyncio
import aiohttp
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

# Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
LANGSEARCH_KEY = os.getenv("LANGSEARCH_KEY")

async def check_telegram():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(f"Telegram: OK (Bot: {data['result']['username']})")
                else:
                    logger.error(f"Telegram: FAILED {data}")
        except Exception as e:
            logger.error(f"Telegram: ERROR {e}")

async def check_deepseek():
    url = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info("Deepseek: OK")
                else:
                    text = await resp.text()
                    logger.error(f"Deepseek: FAILED {resp.status} {text}")
        except Exception as e:
            logger.error(f"Deepseek: ERROR {e}")

async def check_groq():
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    logger.info("Groq: OK")
                else:
                    text = await resp.text()
                    logger.error(f"Groq: FAILED {resp.status} {text}")
        except Exception as e:
            logger.error(f"Groq: ERROR {e}")

async def check_langsearch():
    url = "https://api.langsearch.com/v1/web-search"
    headers = {"Authorization": f"Bearer {LANGSEARCH_KEY}", "Content-Type": "application/json"}
    payload = {
        "query": "test",
        "count": 1
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    logger.info("LangSearch: OK")
                else:
                    text = await resp.text()
                    logger.error(f"LangSearch: FAILED {resp.status} {text}")
        except Exception as e:
            logger.error(f"LangSearch: ERROR {e}")

async def main():
    await asyncio.gather(
        check_telegram(),
        check_deepseek(),
        check_groq(),
        check_langsearch()
    )

if __name__ == "__main__":
    asyncio.run(main())
