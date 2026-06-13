-- Initial schema for the research/harvester orchestration project.

create extension if not exists vector;

-- Sites/feeds/queries to monitor on a recurring basis.
create table public.sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  url text not null,
  source_type text not null check (source_type in ('html', 'rss', 'api', 'sitemap')),
  topic text,
  tags text[] not null default '{}',
  scrape_config jsonb not null default '{}',
  is_active boolean not null default true,
  last_run_at timestamptz,
  created_at timestamptz not null default now()
);

create index sources_is_active_idx on public.sources (is_active);
create index sources_tags_idx on public.sources using gin (tags);

-- One row per orchestration run (scheduled or manual).
create table public.runs (
  id uuid primary key default gen_random_uuid(),
  trigger text not null check (trigger in ('scheduled', 'manual')) default 'manual',
  status text not null check (status in ('running', 'completed', 'failed')) default 'running',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  notes text
);

-- Search queries executed during a run to find new/updated content.
create table public.search_queries (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.runs (id) on delete cascade,
  query text not null,
  result_count integer not null default 0,
  executed_at timestamptz not null default now()
);

create index search_queries_run_id_idx on public.search_queries (run_id);

-- Harvested content, from either a configured source (scrape) or a search result.
create table public.documents (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.runs (id) on delete set null,
  source_id uuid references public.sources (id) on delete set null,
  origin text not null check (origin in ('scrape', 'search')),
  url text not null,
  title text,
  content text,
  content_hash text not null,
  published_at timestamptz,
  fetched_at timestamptz not null default now(),
  metadata jsonb not null default '{}',
  unique (content_hash)
);

create index documents_source_id_idx on public.documents (source_id);
create index documents_run_id_idx on public.documents (run_id);
create index documents_url_idx on public.documents (url);

-- Vector embeddings per document, for dedup/similarity search.
-- Dimension 768 matches Ollama's nomic-embed-text; adjust if you use a different embedding model.
create table public.document_embeddings (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents (id) on delete cascade,
  model text not null,
  embedding vector(768) not null,
  created_at timestamptz not null default now(),
  unique (document_id, model)
);

create index document_embeddings_embedding_idx
  on public.document_embeddings using hnsw (embedding vector_cosine_ops);

-- LLM-generated summaries / extracted insights, per document or per run.
create table public.research_notes (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.runs (id) on delete set null,
  document_id uuid references public.documents (id) on delete cascade,
  summary text,
  key_points jsonb not null default '[]',
  model text not null,
  created_at timestamptz not null default now()
);

create index research_notes_run_id_idx on public.research_notes (run_id);
create index research_notes_document_id_idx on public.research_notes (document_id);
