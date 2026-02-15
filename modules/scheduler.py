from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
scheduler.start()

# Callback function to send messages
_notification_callback = None

def set_notification_callback(func):
    global _notification_callback
    _notification_callback = func

async def _trigger_notification(chat_id: int, message: str):
    if _notification_callback:
        await _notification_callback(chat_id, message)
    else:
        logger.warning(f"Notification triggered but no callback set: {message}")

async def add_reminder(chat_id: int, message: str, delay_seconds: int):
    """
    Adds a reminder for a specific chat.
    """
    try:
        run_date = datetime.now() + timedelta(seconds=delay_seconds)
        scheduler.add_job(_trigger_notification, 'date', run_date=run_date, args=[chat_id, message])
        return f"Reminder set for {run_date.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        logger.error(f"Error adding reminder: {e}")
        return f"Error: {e}"
