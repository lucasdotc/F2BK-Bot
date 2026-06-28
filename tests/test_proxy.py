import httpx
import os

client = httpx.Client()
ANTHROPIC_API_KEY = ""

# Test 1 - should be MISS
r1 = client.post(
    "http://localhost:8000/v1/messages",
    headers={
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    }
)
print("Test 1:", r1.headers.get("x-cache"), "-", r1.json().get("content", [{}])[0].get("text", ""))

# Test 2 - should be HIT
r2 = client.post(
    "http://localhost:8000/v1/messages",
    headers={
        "x-api-key": ANTHROPIC_API_KEY,
        "Content-Type": "application/json",
    },
    json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Tell me France's capital city."}],
    }
)
print("Test 2:", r2.headers.get("x-cache"), "-", r2.json().get("content", [{}])[0].get("text", ""))