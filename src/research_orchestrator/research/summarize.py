import json

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

PROMPT_TEMPLATE = """You are a research assistant. Read the following article and respond with JSON only.

Article title: {title}

Article content:
{content}

Respond with a JSON object containing:
- "summary": a 2-4 sentence summary of the article
- "key_points": a list of 3-6 short bullet-point strings with the most important facts or findings
"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "key_points"],
}

MAX_CONTENT_CHARS = 12000


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def summarize(content: str, title: str | None = None, model: str | None = None) -> dict:
    model = model or settings.ollama_chat_model
    prompt = PROMPT_TEMPLATE.format(title=title or "(untitled)", content=content[:MAX_CONTENT_CHARS])

    resp = httpx.post(
        f"{settings.ollama_host}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": RESPONSE_SCHEMA,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return json.loads(resp.json()["response"])
