import aiohttp
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
LANGSEARCH_KEY = os.getenv("LANGSEARCH_KEY")

async def search_web(query: str, count: int = 5) -> str:
    """
    Searches the web using LangSearch API.
    Returns formatted results.
    """
    url = "https://api.langsearch.com/v1/web-search"
    headers = {"Authorization": f"Bearer {LANGSEARCH_KEY}", "Content-Type": "application/json"}
    payload = {
        "query": query,
        "count": count,
        "freshness": "noLimit",
        "summary": True
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("webPages", {}).get("value", [])
                    if not results:
                        return "No results found."

                    formatted = []
                    for res in results:
                        formatted.append(f"- [{res.get('name')}]({res.get('url')}): {res.get('snippet')}")
                    return "\n".join(formatted)
                else:
                    return f"Error searching: {resp.status}"
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Error: {e}"
