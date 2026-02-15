import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import RetryAfter, TimedOut

logger = logging.getLogger(__name__)

class MessageStreamer:
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
        self.message = None
        self.last_text = ""
        self.buffer = ""
        self.running = False
        self._update_task = None

    async def start(self, initial_text="Thinking..."):
        self.message = await self.update.message.reply_text(initial_text)
        self.last_text = initial_text
        self.running = True
        self._update_task = asyncio.create_task(self._loop())

    async def update(self, text: str):
        self.buffer = text

    async def stop(self):
        self.running = False
        if self._update_task:
            await self._update_task
        # Final update to ensure consistency
        if self.buffer and self.buffer != self.last_text:
            try:
                await self.message.edit_text(self.buffer)
            except Exception as e:
                logger.error(f"Final update failed: {e}")

    async def _loop(self):
        while self.running:
            await asyncio.sleep(1.5) # Telegram rate limits are strict. 1.5s is safe.
            if self.buffer and self.buffer != self.last_text:
                try:
                    await self.message.edit_text(self.buffer)
                    self.last_text = self.buffer
                except RetryAfter as e:
                    logger.warning(f"Rate limited. Sleeping {e.retry_after}")
                    await asyncio.sleep(e.retry_after)
                except TimedOut:
                    logger.warning("Update timed out")
                except Exception as e:
                    # MessageNotModified is common if content is same
                    if "Message is not modified" not in str(e):
                        logger.error(f"Stream update failed: {e}")
