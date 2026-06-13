import hashlib
from datetime import datetime, timezone

from postgrest.exceptions import APIError
from supabase import Client, create_client

from ..config import settings
from .models import Entity, Source

UNIQUE_VIOLATION = "23505"


def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_active_sources(client: Client) -> list[Source]:
    res = client.table("sources").select("*").eq("is_active", True).execute()
    return [Source.from_row(row) for row in res.data]


def get_active_entities(client: Client) -> list[Entity]:
    res = client.table("entities").select("*").eq("is_active", True).execute()
    return [Entity.from_row(row) for row in res.data]


def touch_entity(client: Client, entity_id: str) -> None:
    client.table("entities").update({"last_run_at": datetime.now(timezone.utc).isoformat()}).eq(
        "id", entity_id
    ).execute()


def insert_entity(
    client: Client,
    *,
    name: str,
    entity_type: str,
    query_template: str | None = None,
    cik: str | None = None,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> dict:
    res = client.table("entities").insert(
        {
            "name": name,
            "entity_type": entity_type,
            "query_template": query_template,
            "cik": cik,
            "tags": tags or [],
            "metadata": metadata or {},
        }
    ).execute()
    return res.data[0]


def start_run(client: Client, trigger: str = "manual") -> str:
    res = client.table("runs").insert({"trigger": trigger, "status": "running"}).execute()
    return res.data[0]["id"]


def finish_run(client: Client, run_id: str, status: str = "completed", notes: str | None = None) -> None:
    client.table("runs").update(
        {
            "status": status,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        }
    ).eq("id", run_id).execute()


def touch_source(client: Client, source_id: str) -> None:
    client.table("sources").update({"last_run_at": datetime.now(timezone.utc).isoformat()}).eq(
        "id", source_id
    ).execute()


def log_search_query(
    client: Client, run_id: str, query: str, result_count: int, entity_id: str | None = None
) -> None:
    client.table("search_queries").insert(
        {"run_id": run_id, "query": query, "result_count": result_count, "entity_id": entity_id}
    ).execute()


def insert_document(
    client: Client,
    *,
    run_id: str | None,
    source_id: str | None,
    origin: str,
    url: str,
    title: str | None,
    content: str,
    published_at: datetime | None = None,
    metadata: dict | None = None,
    entity_id: str | None = None,
) -> dict | None:
    """Insert a harvested document. Returns None if an identical document
    (same content_hash) already exists, so callers can skip re-processing."""
    payload = {
        "run_id": run_id,
        "source_id": source_id,
        "entity_id": entity_id,
        "origin": origin,
        "url": url,
        "title": title,
        "content": content,
        "content_hash": content_hash(content),
        "published_at": published_at.isoformat() if published_at else None,
        "metadata": metadata or {},
    }
    try:
        res = client.table("documents").insert(payload).execute()
        return res.data[0]
    except APIError as exc:
        if exc.code == UNIQUE_VIOLATION:
            return None
        raise


def insert_embedding(client: Client, *, document_id: str, model: str, embedding: list[float]) -> None:
    client.table("document_embeddings").upsert(
        {"document_id": document_id, "model": model, "embedding": embedding},
        on_conflict="document_id,model",
    ).execute()


def insert_research_note(
    client: Client,
    *,
    run_id: str | None,
    document_id: str,
    summary: str,
    key_points: list,
    model: str,
) -> None:
    client.table("research_notes").insert(
        {
            "run_id": run_id,
            "document_id": document_id,
            "summary": summary,
            "key_points": key_points,
            "model": model,
        }
    ).execute()
