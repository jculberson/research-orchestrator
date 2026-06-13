import json
from datetime import datetime

import httpx
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential

from ..db.models import Source
from .base import ScrapedDocument, Scraper

USER_AGENT = "research-orchestrator/0.1 (+local research harvester)"


class HtmlScraper(Scraper):
    """Fetches a single page and extracts the main article content."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    def _fetch_html(self, url: str) -> str:
        resp = httpx.get(
            url,
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        return resp.text

    def fetch_url(self, url: str) -> ScrapedDocument | None:
        html = self._fetch_html(url)
        extracted = trafilatura.extract(
            html, output_format="json", with_metadata=True, url=url
        )
        if not extracted:
            return None

        data = json.loads(extracted)
        if not data.get("text"):
            return None

        published_at = None
        if data.get("date"):
            try:
                published_at = datetime.fromisoformat(data["date"])
            except ValueError:
                published_at = None

        return ScrapedDocument(
            url=url,
            title=data.get("title"),
            content=data["text"],
            published_at=published_at,
            metadata={"author": data.get("author"), "sitename": data.get("sitename")},
        )

    def fetch(self, source: Source) -> list[ScrapedDocument]:
        doc = self.fetch_url(source.url)
        return [doc] if doc else []
