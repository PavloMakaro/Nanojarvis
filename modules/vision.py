import aiohttp
import logging
import os
import asyncio
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
OCR_KEY = os.getenv("OCR_API_KEY")

async def recognize_image(file_path: str) -> str:
    """
    Recognizes text in an image file using OCR.space.
    """
    url = "https://api.ocr.space/parse/image"

    if not os.path.exists(file_path):
        return "Error: File not found."

    try:
        data = aiohttp.FormData()
        data.add_field('apikey', OCR_KEY)
        data.add_field('language', 'eng')
        data.add_field('isOverlayRequired', 'false')

        # Read file
        with open(file_path, 'rb') as f:
            file_content = f.read()

        data.add_field('file', file_content, filename=os.path.basename(file_path))

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("IsErroredOnProcessing"):
                         return f"Error: {result.get('ErrorMessage')}"

                    parsed_results = result.get("ParsedResults", [])
                    if not parsed_results:
                        return "No text found."

                    text = "\n".join([r.get("ParsedText", "") for r in parsed_results])
                    return text.strip() if text else "No text found."
                else:
                    return f"Error OCR: {resp.status}"
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return f"Error: {e}"
