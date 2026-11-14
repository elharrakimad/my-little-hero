-- Run once in the project's SQL editor before deploying the API/frontend.
create table if not exists public.site_events (
  event_id uuid primary key,
  session_id uuid not null,
  event_name text not null check (event_name in ('page_view','heartbeat','creation_started','pack_selected','hero_completed','adventure_selected','preview_started','preview_succeeded','preview_failed','whatsapp_clicked')),
  pack_id integer check (pack_id between 1 and 5),
  duration_ms integer check (duration_ms between 0 and 3600000),
  created_at timestamptz not null default now()
);
create index if not exists site_events_created_at_idx on public.site_events(created_at);
alter table public.site_events enable row level security;
revoke all on public.site_events from anon, authenticated;
grant select, insert, update, delete on public.site_events to service_role;
