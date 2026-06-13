import praw

from ..config import settings
from .base import SearchProvider, SearchResult


class RedditSearchProvider(SearchProvider):
    def __init__(self):
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise RuntimeError("REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET are not configured")

        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )

    def search(self, query: str, count: int = 10) -> list[SearchResult]:
        results = []
        for submission in self.reddit.subreddit("all").search(query, sort="new", limit=count):
            body = submission.selftext or ""
            title = f"[r/{submission.subreddit.display_name}] {submission.title}"
            results.append(
                SearchResult(
                    url=f"https://www.reddit.com{submission.permalink}",
                    title=title,
                    snippet=body[:500],
                    content=f"{submission.title}\n\n{body}".strip(),
                )
            )
        return results
