import json
import re
from datetime import datetime

import httpx
import trafilatura
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..scraper.base import ScrapedDocument

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

REPORTING_OWNER_RE = re.compile(r'companyName">([^<(]+)\s*\(<a[^>]*>Reporting', re.IGNORECASE)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def _get(url: str) -> httpx.Response:
    resp = httpx.get(
        url,
        headers={"User-Agent": settings.sec_user_agent},
        timeout=30,
        follow_redirects=True,
    )
    resp.raise_for_status()
    return resp


def _accession_no_dashes(accession_number: str) -> str:
    return accession_number.replace("-", "")


def _filing_index_url(cik: str, accession_number: str) -> str:
    return f"{ARCHIVES_BASE}/{int(cik)}/{accession_number}-index.htm"


def _filing_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    # `primaryDocument` already includes any rendering path prefix (e.g.
    # "xslF345X06/..." for Form 4), so just join it under the accession dir.
    return f"{ARCHIVES_BASE}/{int(cik)}/{_accession_no_dashes(accession_number)}/{primary_document}"


def get_recent_filings(cik: str, forms: list[str], limit: int = 10) -> list[dict]:
    """Return the most recent filings of the given forms for a company CIK."""
    cik_padded = str(cik).zfill(10)
    resp = _get(SUBMISSIONS_URL.format(cik=cik_padded))
    recent = resp.json()["filings"]["recent"]

    filings = []
    for i, form in enumerate(recent["form"]):
        if form not in forms:
            continue
        filings.append(
            {
                "cik": str(cik),
                "form": form,
                "accession_number": recent["accessionNumber"][i],
                "filing_date": recent["filingDate"][i],
                "primary_document": recent["primaryDocument"][i],
            }
        )
        if len(filings) >= limit:
            break
    return filings


def _reporting_owner_name(cik: str, accession_number: str) -> str | None:
    try:
        resp = _get(_filing_index_url(cik, accession_number))
    except Exception:
        return None
    match = REPORTING_OWNER_RE.search(resp.text)
    return match.group(1).strip() if match else None


def fetch_filing_document(filing: dict) -> ScrapedDocument | None:
    """Fetch and extract the content of a filing returned by get_recent_filings."""
    cik = filing["cik"]
    accession_number = filing["accession_number"]
    form = filing["form"]
    primary_document = filing["primary_document"]

    url = _filing_document_url(cik, accession_number, primary_document)

    try:
        resp = _get(url)
    except Exception:
        return None

    extracted = trafilatura.extract(resp.text, output_format="json", with_metadata=True, url=url)
    if not extracted:
        return None

    data = json.loads(extracted)
    if not data.get("text"):
        return None

    title = data.get("title") or f"Form {form} filing ({filing['filing_date']})"
    metadata = {
        "form": form,
        "accession_number": accession_number,
        "filing_date": filing["filing_date"],
        "cik": cik,
    }

    if form == "4":
        owner = _reporting_owner_name(cik, accession_number)
        if owner:
            metadata["reporting_owner"] = owner
            title = f"Form 4 - {owner} ({filing['filing_date']})"

    published_at = None
    try:
        published_at = datetime.fromisoformat(filing["filing_date"])
    except ValueError:
        pass

    return ScrapedDocument(url=url, title=title, content=data["text"], published_at=published_at, metadata=metadata)
