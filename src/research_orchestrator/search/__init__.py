import logging

from ..config import settings
from .base import SearchProvider, SearchResult
from .brave import BraveSearchProvider
from .reddit import RedditSearchProvider

logger = logging.getLogger(__name__)


def get_search_providers() -> list[SearchProvider]:
    providers: list[SearchProvider] = []
    for name in settings.search_providers.split(","):
        name = name.strip().lower()
        if not name:
            continue
        try:
            if name == "brave":
                providers.append(BraveSearchProvider())
            elif name == "reddit":
                providers.append(RedditSearchProvider())
            else:
                logger.warning("Unknown search provider: %s", name)
        except Exception:
            logger.exception("Failed to initialize search provider: %s", name)
    return providers


__all__ = [
    "SearchProvider",
    "SearchResult",
    "BraveSearchProvider",
    "RedditSearchProvider",
    "get_search_providers",
]
