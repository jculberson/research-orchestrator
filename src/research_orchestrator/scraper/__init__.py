from ..db.models import Source
from .base import ScrapedDocument, Scraper
from .html_scraper import HtmlScraper
from .rss_scraper import RssScraper


def get_scraper(source: Source) -> Scraper:
    if source.source_type == "rss":
        return RssScraper()
    if source.source_type in ("html", "sitemap"):
        return HtmlScraper()
    raise ValueError(f"Unsupported source_type: {source.source_type}")


__all__ = ["ScrapedDocument", "Scraper", "HtmlScraper", "RssScraper", "get_scraper"]
