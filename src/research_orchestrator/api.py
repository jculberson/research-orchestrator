import logging

from fastapi import FastAPI
from pydantic import BaseModel

from .pipeline.run import process_manual_submission, run as run_pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Research Orchestrator")


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
