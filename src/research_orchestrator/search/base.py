from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    # If set, used directly as document content instead of fetching `url`
    # (e.g. Reddit post text, which isn't worth re-scraping).
    content: str | None = None


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, count: int = 10) -> list[SearchResult]:
        """Run a web search and return results."""
