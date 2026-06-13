import feedparser

from ..db.models import Source
from .base import ScrapedDocument, Scraper
from .html_scraper import HtmlScraper


class RssScraper(Scraper):
    """Reads an RSS/Atom feed and fetches the full article for each entry."""

    def __init__(self, max_entries: int = 20):
        self.max_entries = max_entries
        self._html_scraper = HtmlScraper()

    def fetch(self, source: Source) -> list[ScrapedDocument]:
        feed = feedparser.parse(source.url)
        docs: list[ScrapedDocument] = []

        for entry in feed.entries[: self.max_entries]:
            link = entry.get("link")
            if not link:
                continue
            try:
                doc = self._html_scraper.fetch_url(link)
            except Exception:
                continue
            if doc:
                docs.append(doc)

        return docs
