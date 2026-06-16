"""
Run the RAG pipeline interactively without Telegram.

Usage:
    set ANTHROPIC_API_KEY=sk-...
    python test_pipeline.py
"""

import os
import sys
import io
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

# Telegram token is not needed here — set a dummy value so bot.py doesn't crash on import
os.environ.setdefault("TELEGRAM_TOKEN", "dummy")

# Import the agent and tool directly from bot.py
from bot import agent, retrieve_sop  # noqa: E402 — must come after env setup

conversation: list[dict] = []


def chat(user_input: str) -> str:
    conversation.append({"role": "user", "content": user_input})
    if len(conversation) > 20:
        conversation[:] = conversation[-20:]

    result = agent.invoke({"messages": conversation})
    reply = result["messages"][-1].content

    conversation.append({"role": "assistant", "content": reply})
    return reply


def test_retrieval(query: str):
    """Print raw vector-store results for a query."""
    print("\n--- Retrieved chunks ---")
    print(retrieve_sop.invoke(query))
    print("------------------------\n")


if __name__ == "__main__":
    print("RAG pipeline test — type your message, or:")
    print("  /retrieve <query>  — show raw vector-store results")
    print("  /reset             — clear conversation history")
    print("  /quit              — exit\n")

    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not line:
            continue
        if line == "/quit":
            break
        if line == "/reset":
            conversation.clear()
            print("Conversation cleared.\n")
            continue
        if line.startswith("/retrieve "):
            test_retrieval(line[len("/retrieve "):])
            continue

        reply = chat(line)
        print(f"\nBot: {reply}\n")
