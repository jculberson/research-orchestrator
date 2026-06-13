# Research Orchestrator

A modular content scraper / "what's new" research harvester, backed by a local
Supabase (Postgres + pgvector) instance and Ollama for embeddings + summarization.

Originally built as a generic harvester, it has been extended into a Workday
intelligence pipeline: in addition to monitoring configured `sources`, it tracks a
list of `entities` (the company itself, officers, partners, competitors, and topics)
and runs searches + SEC EDGAR filing checks for each one every run.

## Architecture

```
n8n (schedule)  --HTTP-->  orchestrator API (FastAPI, Docker)
                                  |
                                  |-- scraper/   (HTML / RSS fetchers, trafilatura extraction)
                                  |-- search/    (Brave Search, Reddit - "what's new" queries)
                                  |-- edgar/     (SEC EDGAR filings: 8-K, Form 4)
                                  |-- research/  (Ollama: embeddings + summarization)
                                  |-- db/        (Supabase client, dedup, persistence)
                                  v
                         Supabase Postgres (sources, entities, runs, documents,
                         document_embeddings (pgvector), research_notes,
                         search_queries)
```

Each piece is swappable:
- Add a new scraper by implementing `Scraper` in `src/research_orchestrator/scraper/` and
  registering it in `get_scraper()`.
- Add a new search backend by implementing `SearchProvider` in
  `src/research_orchestrator/search/` and registering it in `get_search_providers()`.
- Swap embedding/chat models via `.env` (`OLLAMA_EMBED_MODEL`, `OLLAMA_CHAT_MODEL`). Note:
  the `document_embeddings.embedding` column is `vector(768)`, matching
  `nomic-embed-text`. If you switch embedding models, update that column's dimension
  in a new migration.

## Local setup

1. **Supabase** (local CLI, runs as Docker containers):
   ```
   npx supabase start   # Studio at http://127.0.0.1:54323
   npx supabase db reset  # applies migrations in supabase/migrations/
   ```

2. **Python env** (for local CLI use / development):
   ```
   python -m venv .venv
   .venv/Scripts/pip install -e .
   cp .env.example .env   # fill in SUPABASE_SERVICE_KEY (from `supabase status`) and BRAVE_API_KEY
   ```

3. **Add sources to monitor**:
   ```
   research-orchestrator add-source "Some Blog" "https://example.com/blog/feed" --type rss --topic "topic name" --tags ai news
   research-orchestrator add-source "Some Page" "https://example.com/article" --type html
   ```
   - `--type` is `html` (single page), `rss` (feed -> fetches each entry), `sitemap`/`api` reserved for future scrapers.
   - `--topic` (optional) also triggers a web search for "<topic> news" each run, to catch
     new content beyond the configured sources.

4. **Run once manually**:
   ```
   research-orchestrator run
   ```

## Search providers

`SEARCH_PROVIDERS` in `.env` is a comma-separated list (e.g. `brave,reddit`). Each
configured provider runs for every topic-bearing source and every entity. A provider
that fails to initialize (missing/invalid credentials) or fails at search time is
logged and skipped - it won't block the other providers or the rest of the run.

- **Brave Search** (`brave`): set `BRAVE_API_KEY`.
- **Reddit** (`reddit`): create a "script" app at https://www.reddit.com/prefs/apps,
  then set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`. Searches `r/all` and uses the
  post title + body directly (no extra page fetch).

## Entities: tracking Workday, officers, partners, competitors, and topics

The `entities` table (see `supabase/migrations/20260613044503_workday_intel_expansion.sql`)
holds "things to watch" that aren't scrape targets themselves. Each active run:

1. Runs `entity.search_query()` (the entity's `query_template` formatted with `{name}`,
   defaulting to `"{name} Workday"`) across all configured search providers.
2. For `entity_type = "company"` entities with a `cik` set, fetches recent SEC EDGAR
   filings (default forms: `8-K`, `4`) via `edgar/client.py` and processes each as a
   `filing` document.

Every resulting document is embedded, summarized, and tagged with `entity_id` so you
can query "everything about Aneel Bhusri" or "every Form 4 filing this quarter" from
Supabase Studio or via `document_embeddings` similarity search.

### Seeding the Workday entity set

`scripts/seed_workday_entities.py` seeds a starter set: Workday (company, CIK 1327811,
tracking 8-K/Form 4 filings), key officers, major partners (Deloitte, Accenture, PwC,
KPMG, Collaborative Solutions, IBM), competitors (SAP SuccessFactors, Oracle Cloud HCM,
ServiceNow, UKG, Ceridian Dayforce), and broad topics (Workday Ventures, AI Agents,
Workday Rising, user groups, acquisitions, customers, Marketplace, layoffs).

```
.venv/Scripts/python scripts/seed_workday_entities.py
```

It has no upsert logic - check the `entities` table in Studio before re-running to avoid
duplicates.

### Adding more entities via CLI

```
research-orchestrator add-entity "Some Partner Inc" --type partner --query-template "{name} Workday partnership" --tags partner
research-orchestrator add-entity "Some Competitor" --type competitor --tags competitor
research-orchestrator add-entity "Jane Officer" --type officer --tags officer
research-orchestrator add-entity "Some Topic" --type topic --query-template "Workday {name} news"
research-orchestrator add-entity "Another Co" --type company --cik 0000123456 --filing-forms 8-K 4 SC 13D
```

`--type` must be one of `company`, `officer`, `partner`, `competitor`, `topic`.
Set `is_active = false` on a row in Supabase Studio to pause tracking without deleting it.

## SEC EDGAR filings

`src/research_orchestrator/edgar/client.py` fetches a company's recent filings from
`data.sec.gov/submissions/CIK{cik}.json` and extracts the rendered filing content
(via trafilatura). Form 4 (insider buy/sell) filings also get the reporting owner's
name extracted from the filing index page and included in the title/metadata.

Requires `SEC_USER_AGENT` in `.env` to be a descriptive string with contact info
(SEC blocks generic User-Agents), e.g. `research-orchestrator your-email@example.com`.

## Manual inbox (LinkedIn and anything else you want to save by hand)

Automating LinkedIn scraping is high-risk (account bans, ToS violations), so LinkedIn
posts are handled via a **manual feed**: you forward/paste a post's text, and the
orchestrator stores, embeds, and summarizes it like any other document - no browser
automation, no LinkedIn API/session involved.

- **API**: `POST /manual` with JSON body `{"url": "...", "title": "...", "content": "...", "tags": ["linkedin", "partner"]}`.
  Returns `{"status": "ok", "document_id": "..."}` or `{"status": "duplicate"}` if the
  same content was already submitted.
- **n8n form**: import [`n8n/linkedin-manual-inbox-workflow.json`](n8n/linkedin-manual-inbox-workflow.json).
  It's a Form Trigger (gives you a shareable form URL/bookmark) -> `POST /manual`. Paste
  the post URL, title (optional), the post text, and comma-separated tags.

Documents from this path have `origin = "manual"` and no `entity_id` by default - tag
them (e.g. `partner`, `competitor`, `linkedin`) so they're easy to filter later.

## Running via Docker + n8n

```
docker compose up -d --build
```

This starts the orchestrator API on `http://localhost:8000`, reachable from other
containers (including n8n) via `http://host.docker.internal:8000`.

Import these workflows into n8n:
- [`n8n/research-orchestrator-workflow.json`](n8n/research-orchestrator-workflow.json) -
  Schedule Trigger (every 6h) -> HTTP Request `POST /runs`. Adjust the schedule and
  timeout as needed - a run with many sources and entities can take a while since each
  new document is embedded and summarized via Ollama.
- [`n8n/linkedin-manual-inbox-workflow.json`](n8n/linkedin-manual-inbox-workflow.json) -
  manual LinkedIn/notes inbox form (see above).

## Database schema

See `supabase/migrations/`. Key tables:
- `sources` - sites/feeds to monitor (active flag, topic, tags, scrape config)
- `entities` - companies/officers/partners/competitors/topics to search + (for
  companies) track SEC filings for
- `runs` - one row per orchestration run
- `documents` - harvested content, deduped by `content_hash`; `origin` is one of
  `scrape`, `search`, `manual`, `filing`; optionally linked to a `source_id` or `entity_id`
- `document_embeddings` - pgvector embeddings for similarity/dedup
- `research_notes` - LLM-generated summaries + key points per document
- `search_queries` - log of "what's new" search queries per run, optionally linked to an `entity_id`

Browse/query data in Supabase Studio at `http://127.0.0.1:54323`.
