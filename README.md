# F2BK Bot

A private Telegram bot for daycare staff assistance. It uses RAG (retrieval-augmented generation) to answer questions about internal SOPs and processes, and can also calculate teacher payroll deductions — all powered by Claude and LangChain.

## Features

- Answers questions about internal processes (child/teacher onboarding & offboarding, invoicing) via a RAG pipeline over indexed Markdown SOPs
- **Admin mode switcher** — admins get an inline keyboard on `/start` to choose between **Chatbot** (SOP Q&A) and **Payroll** mode; regular users are locked to Chatbot mode
- **Payroll deductions calculator** — computes Federal tax, Provincial tax (Alberta), CPP, CPP2, EI, net pay, and employer costs using the official CRA T4127 (2026) formulas (semi-monthly pay periods, Claim Code 1)
  - Supports one or many teachers in a single request, with a per-teacher report plus a summary of totals
  - Generates a downloadable CSV of the results
  - **File upload support**: in Payroll mode, admins can send a `.csv` or `.xlsx` roster directly. The file's contents are handed to the Claude agent along with an instruction to read the `total` column as each teacher's gross pay and treat every value as a semi-monthly payment — the LLM interprets the sheet and calls the payroll tool itself
- **Knowledge base sync from a private S3 bucket** (optional) — if configured, SOP `.md` files are pulled from a private S3 (or S3-compatible, e.g. Cloudflare R2) bucket into `knowledge/` before indexing, so SOPs never need to live in a shared deploy volume
- Persistent per-user conversation history (last 20 messages)
- Access-controlled — only whitelisted Telegram user IDs can interact with the bot, with a separate admin allowlist for payroll access
- `/start` to begin, `/reset` to clear conversation history
- Dockerized, with a `docker-compose.yml` for local/VM use and tested for deployment on Railway

## Stack

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [LangChain](https://github.com/langchain-ai/langchain) + Claude (`claude-sonnet-4-6`) via `init_chat_model`
- [Chroma](https://www.trychroma.com/) for vector storage
- [HuggingFace sentence-transformers](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) for embeddings
- [openpyxl](https://openpyxl.readthedocs.io/) for reading `.xlsx` payroll uploads
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) for optional S3 knowledge sync
- [uv](https://github.com/astral-sh/uv) for local dependency management / Docker + pip for deployment

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
   ADMIN_USER_IDS=123456789

   # Optional: sync knowledge/*.md files from a private bucket before indexing.
   # Leave KNOWLEDGE_BUCKET blank to use only the local knowledge/ folder.
   KNOWLEDGE_BUCKET=your-bucket-name
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   # Only needed for an S3-compatible provider other than AWS (e.g. Cloudflare R2):
   # S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   ```

3. **Add SOP files** — place `.md` files in a `knowledge/` folder (or configure `KNOWLEDGE_BUCKET` above). They are automatically indexed into the vector store on startup.

4. **Run the bot**
   ```bash
   python bot.py
   ```
   or, with Docker:
   ```bash
   docker compose up
   ```

## Project Structure

```
├── bot.py                  # Main bot entry point — handlers, agents, tool definitions
├── src/
│   ├── config.py           # Chroma vector store + embeddings setup
│   ├── indexing.py         # SOP indexing pipeline
│   ├── payroll.py          # CRA T4127 payroll calculator, report/CSV formatting, file table extraction
│   └── knowledge_sync.py   # Optional sync of SOP docs from a private S3 bucket
├── tests/
│   ├── test_pipeline.py
│   └── test_proxy.py
├── Dockerfile
├── docker-compose.yml       # chroma_db/, knowledge/, and HF cache mounted as volumes
├── chroma_db/               # Persisted vector store (gitignored)
└── knowledge/               # SOP Markdown files (gitignored, or synced from S3)
```

## Knowledge Indexing

On startup, if `KNOWLEDGE_BUCKET` is set, `sync_knowledge_from_bucket()` first downloads any `.md` objects from that bucket into `knowledge/` (falling back to whatever's already indexed if the sync fails). Then `run_indexing()` scans `knowledge/*.md` and adds any new files to the Chroma vector store — already-indexed files are skipped. The bot uses similarity search over these chunks to answer SOP-related queries.

## Payroll Calculator

Admins in Payroll mode can either:
- Type teacher names and gross pay directly in chat, or
- Upload a `.csv`/`.xlsx` roster — the bot reads the raw file contents and passes them to the agent, which is instructed to use the `total` column as each teacher's semi-monthly gross pay

Either path calls the `calculate_payroll_deductions` tool, which applies the CRA T4127 (2026) formulas for Alberta and returns a detailed report plus a downloadable CSV. Always verify results against the official CRA PDOC before processing real payroll.

## Deployment

The bot is a long-polling process (no inbound HTTP port needed). It's Dockerized and can run on any host that supports `docker compose up`, or on a platform like [Railway](https://railway.app/) connected to this repo for auto-deploy on push — just make sure to configure the environment variables above and provision persistent volumes for `chroma_db/` and the HuggingFace cache (`/root/.cache/huggingface`).
