import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db.client import get_client
from .pipeline.run import process_manual_submission, run as run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Research Orchestrator")

# Allow the local dashboard (file:// or any localhost origin) to read /stats.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    trigger: str = "scheduled"


class ManualSubmission(BaseModel):
    url: str
    title: str | None = None
    content: str
    tags: list[str] = []


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/runs")
def trigger_run(body: RunRequest) -> dict:
    run_id = run_pipeline(trigger=body.trigger)
    return {"run_id": run_id, "status": "completed"}


@app.post("/manual")
def submit_manual(body: ManualSubmission) -> dict:
    """Ingest a manually-saved item, e.g. a LinkedIn post forwarded by the user."""
    document_id = process_manual_submission(url=body.url, title=body.title, content=body.content, tags=body.tags)
    if document_id is None:
        return {"status": "duplicate"}
    return {"status": "ok", "document_id": document_id}


@app.get("/stats")
def stats() -> dict:
    """Read-only summary for the dashboard: entity/document/note totals,
    breakdowns by type and origin, and the most recent harvested documents."""
    client = get_client()
    totals = client.table("research_totals").select("*").execute().data[0]
    by_type = {r["entity_type"]: r["count"] for r in client.table("research_entity_type_counts").select("*").execute().data}
    by_origin = {r["origin"]: r["count"] for r in client.table("research_doc_origin_counts").select("*").execute().data}
    recent = client.table("research_recent_documents").select("*").execute().data
    last = (
        client.table("runs")
        .select("trigger,status,started_at,finished_at")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return {
        "entities": totals["entities"],
        "documents": totals["documents"],
        "notes": totals["notes"],
        "entities_by_type": by_type,
        "documents_by_origin": by_origin,
        "recent_documents": recent,
        "last_run": last[0] if last else None,
    }
