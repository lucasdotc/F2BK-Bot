# F2BK Bot

A private Telegram bot for daycare staff assistance. It uses RAG (retrieval-augmented generation) to answer questions about internal SOPs and processes, powered by Claude and LangChain.

## Features

- Answers questions about internal processes (child/teacher onboarding & offboarding, invoicing)
- RAG pipeline: indexes Markdown SOP files into a Chroma vector store and retrieves relevant context per query
- Persistent per-user conversation history (last 20 messages)
- Access-controlled — only whitelisted Telegram user IDs can interact with the bot
- `/start` to begin, `/reset` to clear conversation history

## Stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [LangChain](https://github.com/langchain-ai/langchain) + Claude (`claude-sonnet-4-6`) via `init_chat_model`
- [Chroma](https://www.trychroma.com/) for vector storage
- [HuggingFace sentence-transformers](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) for embeddings
- [uv](https://github.com/astral-sh/uv) for dependency management

## Setup

1. **Install dependencies**
   ```bash
   uv sync
   ```

2. **Configure environment variables** — create a `.env` file:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ALLOWED_USER_IDS=123456789,987654321
   ```

3. **Add SOP files** — place `.md` files in a `knowledge/` folder. They will be automatically indexed into the vector store on startup.

4. **Run the bot**
   ```bash
   python bot.py
   ```

## Project Structure

```
├── bot.py              # Main bot entry point
├── src/
│   ├── config.py       # Chroma vector store setup
│   └── indexing.py     # SOP indexing pipeline
├── tests/
│   └── test_pipeline.py
├── chroma_db/          # Persisted vector store (gitignored)
└── knowledge/          # SOP Markdown files (gitignored)
```

## Knowledge Indexing

On startup, `run_indexing()` scans `knowledge/*.md` and adds any new files to the Chroma vector store. Already-indexed files are skipped. The bot uses similarity search over these chunks to answer SOP-related queries.
