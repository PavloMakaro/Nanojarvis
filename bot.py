import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from agent.core import Agent
from agent.llm import LLMClient
from agent.memory import ConversationMemory
from utils.telegram_utils import MessageStreamer
import os
from dotenv import load_dotenv

load_dotenv()

# Import Modules
from modules import web_search, vision, scheduler, diary, module_generator

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# API Keys
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
if TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip()
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    logging.critical("BOT_TOKEN is missing or empty in .env")
    exit(1)

# Initialize Agent
llm_client = LLMClient(DEEPSEEK_KEY, GROQ_KEY)
memory = ConversationMemory()
agent = Agent(llm_client, memory)

# Register Tools
agent.register_tool("search_web", web_search.search_web, "Search the web. Args: query (str), count (int, default 5).")
agent.register_tool("recognize_image", vision.recognize_image, "Recognize text in an image. Args: file_path (str).")
agent.register_tool("write_diary", diary.write_diary, "Write to diary. Args: entry (str).")
agent.register_tool("read_diary", diary.read_diary, "Read diary. Args: lines (int, default 5).")
agent.register_tool("add_reminder", scheduler.add_reminder, "Add reminder. Args: chat_id (int), message (str), delay_seconds (int).")
agent.register_tool("create_module", module_generator.create_module, "Create python module. Args: filename (str), code (str).")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memory.clear()
    await update.message.reply_text("Hello! I am GarvisClaw. How can I help you today?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    # Create streamer
    streamer = MessageStreamer(update, context)
    await streamer.start("Thinking...")

    async def callback(text, is_status):
        if is_status:
            await streamer.update(f"⏳ {text}")
        else:
            if not text:
                return
            await streamer.update(text)

    # Inject chat_id for scheduler if user mentions reminder
    # Or just let agent ask for it?
    # Better: Append context info to prompt.
    chat_id = update.effective_chat.id
    # We can prepend this to system prompt or user message.
    # But `agent.process` takes string.
    # We'll just append it to user text internally if needed, or rely on agent knowing it?
    # Agent doesn't know chat_id unless passed.
    # Let's append: "[Context: chat_id={chat_id}]"

    full_text = f"{user_text}\n[System Context: chat_id={chat_id}]"

    try:
        await agent.process(full_text, update_callback=callback)
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        await streamer.update(f"An error occurred: {e}")
    finally:
        await streamer.stop()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    file_path = f"photo_{update.message.id}.jpg"
    await photo_file.download_to_drive(file_path)

    streamer = MessageStreamer(update, context)
    await streamer.start("Analyzing image...")

    async def callback(text, is_status):
        if is_status:
            await streamer.update(f"⏳ {text}")
        else:
            if not text: return
            await streamer.update(text)

    prompt = f"I sent an image. It is saved at: {file_path}. Please analyze it using recognize_image tool."

    try:
        await agent.process(prompt, update_callback=callback)
    except Exception as e:
        logging.error(f"Error processing photo: {e}")
        await streamer.update(f"An error occurred: {e}")
    finally:
        await streamer.stop()

async def post_init(application):
    scheduler.start_scheduler()

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # Setup Scheduler Callback
    async def notification_sender(chat_id, message):
        try:
            await application.bot.send_message(chat_id=chat_id, text=f"⏰ Reminder: {message}")
        except Exception as e:
            logging.error(f"Failed to send reminder: {e}")

    scheduler.set_notification_callback(notification_sender)

    start_handler = CommandHandler('start', start)
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    photo_handler = MessageHandler(filters.PHOTO, handle_photo)

    application.add_handler(start_handler)
    application.add_handler(msg_handler)
    application.add_handler(photo_handler)

    print("Bot is running...")
    application.run_polling()
