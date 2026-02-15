import os
import datetime
import logging

DIARY_FILE = "user_diary.txt"

logger = logging.getLogger(__name__)

async def write_diary(entry: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DIARY_FILE, "a") as f:
        f.write(f"[{timestamp}] {entry}\n")
    return "Entry added to diary."

async def read_diary(lines: int = 5):
    if not os.path.exists(DIARY_FILE):
        return "Diary is empty."
    with open(DIARY_FILE, "r") as f:
        content = f.readlines()
    return "".join(content[-lines:])
