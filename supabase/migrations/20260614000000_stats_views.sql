-- Aggregate views for the Research dashboard /stats endpoint.
-- Small result sets, so they sidestep the PostgREST 1000-row response cap.

create or replace view public.research_totals as
select
  (select count(*) from public.entities)::int       as entities,
  (select count(*) from public.documents)::int       as documents,
  (select count(*) from public.research_notes)::int   as notes;

create or replace view public.research_entity_type_counts as
select entity_type, count(*)::int as count
from public.entities
group by entity_type
order by count desc;

create or replace view public.research_doc_origin_counts as
select origin, count(*)::int as count
from public.documents
group by origin
order by count desc;

create or replace view public.research_recent_documents as
select d.id, d.title, d.origin, d.url, d.published_at, d.fetched_at, e.name as entity
from public.documents d
left join public.entities e on e.id = d.entity_id
order by d.fetched_at desc
limit 10;

grant select on public.research_totals to service_role;
grant select on public.research_entity_type_counts to service_role;
grant select on public.research_doc_origin_counts to service_role;
grant select on public.research_recent_documents to service_role;
