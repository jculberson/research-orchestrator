/* ============================================================================
   DOWNSTREAM REPOSITORY (PostgreSQL + pgvector)  —  what the tool iterates over
   ----------------------------------------------------------------------------
   The Polaris `ai.*` views (SQL Server, see polaris-ai-views.sql) are the
   source of truth. A sync job copies the denormalized discovery rows here and
   embeds them, so the assistant can do fast semantic + keyword search without
   hammering the ILS. This mirrors the stack already used in this repo
   (Supabase Postgres + pgvector + Ollama embeddings, e.g. nomic-embed-text/768).

   Split of duties:
     * Catalog METADATA + embeddings  -> synced nightly / on bib-change (here).
     * Live AVAILABILITY + hold counts -> read at query time from the SQL Server
       views (ai.vwTitleAvailabilityByBranch), never cached for long.
   ============================================================================ */

CREATE EXTENSION IF NOT EXISTS vector;

-- One row per title; metadata snapshot + embedding for retrieval.
CREATE TABLE IF NOT EXISTS catalog_titles (
    bib_id            bigint PRIMARY KEY,        -- = Polaris BibliographicRecordID
    title             text NOT NULL,
    author            text,
    format            text,
    audience          text,                      -- reading level / target age
    isbn              text,
    published         text,
    subjects          text,
    summary           text,
    search_text       text,                      -- from ai.vwTitleDiscovery.search_text
    embedding         vector(768),               -- nomic-embed-text dimension
    -- denormalized convenience copies, refreshed on sync (NOT authoritative):
    copies_total      int,
    copies_available  int,                       -- point-in-time; verify live before reserving
    active_holds      int,
    synced_at         timestamptz NOT NULL DEFAULT now()
);

-- Per-branch availability snapshot (optional cache; live view is authoritative).
CREATE TABLE IF NOT EXISTS catalog_availability (
    bib_id            bigint NOT NULL,
    branch_id         int    NOT NULL,
    branch_name       text,
    copies_total      int,
    copies_available  int,
    synced_at         timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (bib_id, branch_id)
);

-- Indexes: semantic (cosine) + keyword fallback.
CREATE INDEX IF NOT EXISTS catalog_titles_embedding_idx
    ON catalog_titles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS catalog_titles_fts_idx
    ON catalog_titles USING gin (to_tsvector('english', coalesce(search_text, '')));

/* ----------------------------------------------------------------------------
   SYNC SKETCH (run nightly or on bib-change webhook):
     1. SELECT bib_id, title, author, ..., search_text FROM ai.vwTitleDiscovery
        on SQL Server  ->  upsert into catalog_titles here.
     2. For changed rows, call the embedding model (Ollama nomic-embed-text)
        on search_text  ->  UPDATE embedding.
     3. Refresh catalog_availability from ai.vwTitleAvailabilityByBranch.
   At QUERY time the assistant: (a) retrieves candidate titles from here, then
   (b) re-checks copies_available for the chosen title against the LIVE SQL Server
   view before offering to place a hold.
   ---------------------------------------------------------------------------- */

-- Example retrieval the tool runs (embedding-based, with availability join):
-- SELECT t.bib_id, t.title, t.author, t.copies_available
-- FROM   catalog_titles t
-- ORDER  BY t.embedding <=> $1     -- $1 = embedded user query
-- LIMIT  10;
