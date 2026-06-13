import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings

# nomic-embed-text has a 2048-token context window; keep well under that
# to avoid Ollama hanging/timing out on long documents.
MAX_EMBED_CHARS = 6000


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def embed(text: str, model: str | None = None) -> list[float]:
    model = model or settings.ollama_embed_model
    resp = httpx.post(
        f"{settings.ollama_host}/api/embeddings",
        json={"model": model, "prompt": text[:MAX_EMBED_CHARS]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]
