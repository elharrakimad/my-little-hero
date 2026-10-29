-- Mirrors the migration applied through Supabase on 2026-10-29.
alter table public.orders
    add column if not exists generation_progress jsonb not null default '{}'::jsonb;
comment on column public.orders.generation_progress is
    'Server-side production progress, timestamps, bounded event history and sanitized errors.';
