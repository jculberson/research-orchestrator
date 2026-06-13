from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from ..db.models import Source


@dataclass
class ScrapedDocument:
    url: str
    title: str | None
    content: str
    published_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


class Scraper(ABC):
    @abstractmethod
    def fetch(self, source: Source) -> list[ScrapedDocument]:
        """Fetch one or more documents for the given source."""
