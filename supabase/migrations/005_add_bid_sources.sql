alter table public.bids
  add column if not exists canonical_source text not null default 'g2b';

comment on column public.bids.canonical_source is
  '중복 판별용 원 출처. 나라장터 재게시 공고는 g2b로 통합한다.';

alter table public.bids
  drop constraint if exists bids_bid_no_bid_order_bid_type_key;

create unique index if not exists bids_canonical_identity_key
  on public.bids (canonical_source, bid_no, bid_order, bid_type);

create table if not exists public.bid_sources (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  source_system text not null,
  source_bid_id text not null,
  source_bid_order text not null default '0',
  source_url text,
  raw_data jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  unique (source_system, source_bid_id, source_bid_order)
);

create index if not exists bid_sources_bid_id_idx
  on public.bid_sources (bid_id);

alter table public.bid_sources enable row level security;

create policy "allowed users read bid sources" on public.bid_sources
  for select to authenticated using (public.is_allowed_user());

-- 2026-10-30부터 신규 public 테이블은 Data API에 자동 노출되지 않으므로
-- 역할별 권한을 명시적으로 부여한다.
grant select on public.bid_sources to authenticated;
grant all privileges on public.bid_sources to service_role;

-- 기존 나라장터 행도 출처 이력에 등록한다.
insert into public.bid_sources (
  bid_id, source_system, source_bid_id, source_bid_order, source_url, raw_data
)
select id, 'g2b', bid_no, bid_order, source_url, raw_data
from public.bids
on conflict (source_system, source_bid_id, source_bid_order) do update
set bid_id = excluded.bid_id,
    source_url = excluded.source_url,
    raw_data = excluded.raw_data,
    last_seen_at = now();
