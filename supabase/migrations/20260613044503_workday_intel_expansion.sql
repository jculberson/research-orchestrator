-- Entities to track via search (and, for companies, SEC EDGAR filings) in
-- addition to scraped sources: officers, partners, competitors, topics.
create table public.entities (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  entity_type text not null check (entity_type in ('company', 'officer', 'partner', 'competitor', 'topic')),
  -- Query template for "what's new" search, e.g. "{name} Workday partnership".
  -- Defaults to "{name} Workday" when null.
  query_template text,
  -- SEC CIK (company only) for EDGAR filing tracking, e.g. Workday = 1327811.
  cik text,
  tags text[] not null default '{}',
  metadata jsonb not null default '{}',
  is_active boolean not null default true,
  last_run_at timestamptz,
  created_at timestamptz not null default now()
);

create index entities_is_active_idx on public.entities (is_active);
create index entities_type_idx on public.entities (entity_type);
create index entities_tags_idx on public.entities using gin (tags);

-- Track which entity a search query / document relates to.
alter table public.search_queries add column entity_id uuid references public.entities (id) on delete cascade;
alter table public.documents add column entity_id uuid references public.entities (id) on delete set null;

-- Broaden document origin to cover manual submissions (e.g. LinkedIn posts saved by
-- the user) and SEC EDGAR filings, in addition to scraping and web search.
alter table public.documents drop constraint documents_origin_check;
alter table public.documents add constraint documents_origin_check
  check (origin in ('scrape', 'search', 'manual', 'filing'));

grant all on public.entities to service_role;
