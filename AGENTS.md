# GarvisClaw Agent

## Architecture
GarvisClaw is a lightweight, modular AI agent designed for Telegram, running on constrained resources (100MB RAM).

### Core Components
- **bot.py**: Entry point. Handles Telegram updates and streams responses.
- **agent/core.py**: Implements the Perceive-Think-Act loop. Supports multi-step reasoning.
- **agent/llm.py**: Async client for Deepseek and Groq APIs.
- **agent/memory.py**: Efficient conversation history management.
- **modules/**: Pluggable skills (Web Search, Vision, Diary, Scheduler, etc.).

## Instructions for Developers
- Keep memory usage low. Avoid heavy imports.
- Use async/await for all I/O.
- Add new tools by creating a module in `modules/` and registering it in `bot.py`.
- Run tests with `PYTHONPATH=. pytest`.

## Usage
- Run `./start.sh` to start the bot.
- Check `user_diary.txt` for diary entries.
