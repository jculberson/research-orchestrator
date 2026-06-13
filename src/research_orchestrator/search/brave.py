import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from .base import SearchProvider, SearchResult

API_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider(SearchProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.brave_api_key
        if not self.api_key:
            raise RuntimeError("BRAVE_API_KEY is not configured")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def search(self, query: str, count: int = 10) -> list[SearchResult]:
        resp = httpx.get(
            API_URL,
            params={"q": query, "count": count},
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(
                SearchResult(
                    url=item["url"],
                    title=item.get("title", ""),
                    snippet=item.get("description", ""),
                )
            )
        return results
