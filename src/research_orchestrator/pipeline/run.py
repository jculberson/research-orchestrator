import logging

from ..config import settings
from ..db.client import (
    finish_run,
    get_active_entities,
    get_active_sources,
    get_client,
    insert_document,
    insert_embedding,
    insert_research_note,
    log_search_query,
    start_run,
    touch_entity,
    touch_source,
)
from ..db.models import Entity, Source
from ..edgar import fetch_filing_document, get_recent_filings
from ..research import embed, summarize
from ..scraper import get_scraper
from ..scraper.base import ScrapedDocument
from ..scraper.html_scraper import HtmlScraper
from ..search import get_search_providers

logger = logging.getLogger(__name__)

# Default SEC form types tracked for "company" entities with a CIK set.
DEFAULT_FILING_FORMS = ["8-K", "4"]
ENTITY_SEARCH_COUNT = 5
FILINGS_PER_RUN = 5


def _process_document(
    client,
    run_id: str | None,
    source_id: str | None,
    origin: str,
    doc: ScrapedDocument,
    entity_id: str | None = None,
) -> str | None:
    row = insert_document(
        client,
        run_id=run_id,
        source_id=source_id,
        entity_id=entity_id,
        origin=origin,
        url=doc.url,
        title=doc.title,
        content=doc.content,
        published_at=doc.published_at,
        metadata=doc.metadata,
    )
    if row is None:
        logger.info("Skipping duplicate document: %s", doc.url)
        return None

    document_id = row["id"]

    try:
        vector = embed(doc.content)
        insert_embedding(client, document_id=document_id, model=settings.ollama_embed_model, embedding=vector)
    except Exception:
        logger.exception("Embedding failed for %s", doc.url)

    try:
        result = summarize(doc.content, title=doc.title)
        insert_research_note(
            client,
            run_id=run_id,
            document_id=document_id,
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            model=settings.ollama_chat_model,
        )
    except Exception:
        logger.exception("Summarization failed for %s", doc.url)

    return document_id


def process_manual_submission(url: str, title: str | None, content: str, tags: list[str] | None = None) -> str | None:
    """Ingest a manually-saved item (e.g. a LinkedIn post the user forwarded).

    Returns the new document id, or None if it's a duplicate of an existing document.
    """
    client = get_client()
    doc = ScrapedDocument(url=url, title=title, content=content, metadata={"tags": tags or []})
    return _process_document(client, run_id=None, source_id=None, origin="manual", doc=doc)


def _run_topic_search(client, run_id: str, source: Source) -> None:
    providers = get_search_providers()
    if not providers:
        logger.warning("No search providers available, skipping topic search")
        return

    query = f"{source.topic} news"
    html_scraper = HtmlScraper()

    for provider in providers:
        try:
            results = provider.search(query)
        except Exception:
            logger.exception("Search failed for query: %s (%s)", query, type(provider).__name__)
            continue

        log_search_query(client, run_id, query, len(results))

        for result in results:
            if result.content is not None:
                doc = ScrapedDocument(url=result.url, title=result.title, content=result.content)
            else:
                try:
                    doc = html_scraper.fetch_url(result.url)
                except Exception:
                    continue
            if doc:
                _process_document(client, run_id, source.id, "search", doc)


def _run_entity_search(client, run_id: str, entity: Entity) -> None:
    providers = get_search_providers()
    if not providers:
        logger.warning("No search providers available, skipping entity search")
        return

    query = entity.search_query()
    html_scraper = HtmlScraper()

    for provider in providers:
        try:
            results = provider.search(query, count=ENTITY_SEARCH_COUNT)
        except Exception:
            logger.exception("Search failed for query: %s (%s)", query, type(provider).__name__)
            continue

        log_search_query(client, run_id, query, len(results), entity_id=entity.id)

        for result in results:
            if result.content is not None:
                doc = ScrapedDocument(url=result.url, title=result.title, content=result.content)
            else:
                try:
                    doc = html_scraper.fetch_url(result.url)
                except Exception:
                    continue
            if doc:
                _process_document(client, run_id, None, "search", doc, entity_id=entity.id)


def _run_entity_filings(client, run_id: str, entity: Entity) -> None:
    if entity.entity_type != "company" or not entity.cik:
        return

    forms = entity.metadata.get("filing_forms", DEFAULT_FILING_FORMS)
    try:
        filings = get_recent_filings(entity.cik, forms=forms, limit=FILINGS_PER_RUN)
    except Exception:
        logger.exception("Failed to fetch SEC filings for entity %s (CIK %s)", entity.name, entity.cik)
        return

    for filing in filings:
        try:
            doc = fetch_filing_document(filing)
        except Exception:
            logger.exception("Failed to fetch filing %s for entity %s", filing["accession_number"], entity.name)
            continue
        if doc:
            _process_document(client, run_id, None, "filing", doc, entity_id=entity.id)


def run(trigger: str = "manual") -> str:
    client = get_client()
    run_id = start_run(client, trigger=trigger)
    logger.info("Started run %s", run_id)

    try:
        for source in get_active_sources(client):
            logger.info("Scraping source %s (%s)", source.name, source.url)
            try:
                scraper = get_scraper(source)
                docs = scraper.fetch(source)
            except Exception:
                logger.exception("Scrape failed for source %s", source.name)
                docs = []

            for doc in docs:
                _process_document(client, run_id, source.id, "scrape", doc)

            if source.topic:
                _run_topic_search(client, run_id, source)

            touch_source(client, source.id)

        for entity in get_active_entities(client):
            logger.info("Processing entity %s (%s)", entity.name, entity.entity_type)
            try:
                _run_entity_search(client, run_id, entity)
                _run_entity_filings(client, run_id, entity)
            except Exception:
                logger.exception("Entity processing failed for %s", entity.name)

            touch_entity(client, entity.id)

        finish_run(client, run_id, status="completed")
    except Exception as exc:
        finish_run(client, run_id, status="failed", notes=str(exc))
        raise

    logger.info("Finished run %s", run_id)
    return run_id


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
