create extension if not exists pgcrypto;

create table if not exists public.bids (
  id uuid primary key default gen_random_uuid(),
  bid_no text not null,
  bid_order text not null default '000',
  title text not null,
  agency text,
  demand_agency text,
  bid_type text not null default '물품',
  contract_method text,
  bid_method text,
  estimated_amount bigint,
  base_amount bigint,
  posted_at timestamptz,
  deadline_at timestamptz,
  opening_at timestamptz,
  source_url text,
  content_hash text,
  matched_keywords jsonb not null default '[]'::jsonb,
  raw_data jsonb,
  status text not null default '신규'
    check (status in (
      '신규','검토중','참여가능','조건확인필요','대표승인필요',
      '제안/견적준비','투찰완료','낙찰','미선정','제외','보류'
    )),
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (bid_no, bid_order, bid_type)
);

create table if not exists public.bid_versions (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  content_hash text not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now(),
  unique (bid_id, content_hash)
);

create table if not exists public.bid_analyses (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null unique references public.bids(id) on delete cascade,
  summary text,
  required_certifications jsonb not null default '[]'::jsonb,
  required_documents jsonb not null default '[]'::jsonb,
  qualification_requirements jsonb not null default '[]'::jsonb,
  region_limit text,
  performance_requirement text,
  delivery_deadline text,
  delivery_location text,
  joint_supply_allowed boolean,
  risk_factors jsonb not null default '[]'::jsonb,
  score_breakdown jsonb not null default '[0,0,0,0,0,0,0]'::jsonb,
  fit_score integer not null default 0 check (fit_score between 0 and 100),
  recommendation text,
  confidence numeric(4,3),
  ai_model text,
  analyzed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.bid_analysis_evidence (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  field_name text not null,
  extracted_value jsonb,
  evidence_text text,
  source_file text,
  page_number integer,
  created_at timestamptz not null default now()
);

create table if not exists public.bid_attachments (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  file_name text not null,
  file_url text,
  storage_path text,
  file_type text,
  content_hash text,
  extracted_text text,
  parse_status text not null default 'pending'
    check (parse_status in ('pending','processing','success','failed','skipped')),
  parse_error text,
  created_at timestamptz not null default now(),
  unique (bid_id, file_name)
);

create table if not exists public.keyword_groups (
  id uuid primary key default gen_random_uuid(),
  group_name text not null unique,
  description text,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.keywords (
  id uuid primary key default gen_random_uuid(),
  group_id uuid references public.keyword_groups(id) on delete cascade,
  keyword text not null,
  match_type text not null default 'include'
    check (match_type in ('include','exclude','synonym')),
  search_fields jsonb not null default '["title","agency","product"]'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  unique (group_id, keyword, match_type)
);

create table if not exists public.bid_keyword_matches (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  keyword_id uuid references public.keywords(id) on delete set null,
  keyword_text text not null,
  matched_field text,
  created_at timestamptz not null default now(),
  unique (bid_id, keyword_text)
);

create table if not exists public.company_profiles (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references auth.users(id) on delete cascade,
  company_name text not null,
  min_amount bigint,
  max_amount bigint,
  allowed_regions jsonb not null default '["전국"]'::jsonb,
  score_weights jsonb not null default
    '{"product":25,"amount":15,"certification":20,"region":10,"delivery":10,"performance":10,"risk":10}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.company_certifications (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.company_profiles(id) on delete cascade,
  certification_name text not null,
  expires_at date,
  created_at timestamptz not null default now(),
  unique (company_id, certification_name)
);

create table if not exists public.company_products (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.company_profiles(id) on delete cascade,
  product_name text not null,
  keywords jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique (company_id, product_name)
);

create table if not exists public.saved_bids (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  memo text,
  assigned_to uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (bid_id, user_id)
);

create table if not exists public.bid_checklists (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  item_key text not null,
  item_label text not null,
  is_checked boolean not null default false,
  checked_at timestamptz,
  created_at timestamptz not null default now(),
  unique (bid_id, user_id, item_key)
);

create table if not exists public.bid_status_history (
  id uuid primary key default gen_random_uuid(),
  bid_id uuid not null references public.bids(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  from_status text,
  to_status text not null,
  reason text,
  created_at timestamptz not null default now()
);

create table if not exists public.collection_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running'
    check (status in ('running','success','failed','partial')),
  fetched_count integer not null default 0,
  matched_count integer not null default 0,
  analyzed_count integer not null default 0,
  error_message text
);

create table if not exists public.collection_errors (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.collection_runs(id) on delete cascade,
  bid_no text,
  stage text not null,
  error_message text not null,
  retry_count integer not null default 0,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists bids_posted_at_idx on public.bids(posted_at desc);
create index if not exists bids_deadline_at_idx on public.bids(deadline_at);
create index if not exists bids_status_idx on public.bids(status);
create index if not exists bids_title_search_idx
  on public.bids using gin (to_tsvector('simple', coalesce(title, '')));

alter table public.bids enable row level security;
alter table public.bid_analyses enable row level security;
alter table public.bid_attachments enable row level security;
alter table public.keyword_groups enable row level security;
alter table public.keywords enable row level security;
alter table public.saved_bids enable row level security;
alter table public.bid_checklists enable row level security;
alter table public.company_profiles enable row level security;

-- 나라장터 공고는 공개정보이므로 비로그인 사용자도 조회만 허용합니다.
create policy "public read bids" on public.bids for select using (true);
create policy "public read analyses" on public.bid_analyses for select using (true);
create policy "public read keyword groups" on public.keyword_groups for select using (true);
create policy "public read keywords" on public.keywords for select using (true);

create policy "users manage own saved bids" on public.saved_bids
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage own checklists" on public.bid_checklists
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "users manage own company" on public.company_profiles
  for all using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- "Automatically expose new tables"를 비활성화한 운영 프로젝트에서는
-- Data API 역할에 필요한 권한을 명시적으로 부여해야 합니다.
grant usage on schema public to anon, authenticated, service_role;

grant select on table
  public.bids,
  public.bid_analyses,
  public.keyword_groups,
  public.keywords
to anon, authenticated;

grant select, insert, update, delete on table
  public.saved_bids,
  public.bid_checklists,
  public.company_profiles
to authenticated;

grant all privileges on all tables in schema public to service_role;
grant all privileges on all sequences in schema public to service_role;

insert into public.keyword_groups (group_name) values
  ('PC·컴퓨터'), ('서버·고성능장비'), ('전산장비'),
  ('네트워크·스토리지'), ('주변기기'), ('교육·강의장비'), ('기타')
on conflict (group_name) do nothing;

insert into public.keywords (group_id, keyword)
select g.id, x.keyword
from public.keyword_groups g
join lateral (
  select unnest(
    case g.group_name
      when 'PC·컴퓨터' then array['컴퓨터','PC','데스크톱','노트북','랩탑','모니터']
      when '서버·고성능장비' then array['서버','SERVER','GPU 서버','워크스테이션','딥러닝']
      when '전산장비' then array['전산장비','전산기기','전산설비','시스템 장비']
      when '네트워크·스토리지' then array['네트워크','스토리지','NAS','SAN','방화벽','스위치']
      when '주변기기' then array['모니터','프린터','스캐너','UPS']
      when '교육·강의장비' then array['전자칠판','인터랙티브 화이트보드','LED 전광판']
      when '기타' then array['소프트웨어','렌탈','리스']
      else array[]::text[]
    end
  ) keyword
) x on true
on conflict (group_id, keyword, match_type) do nothing;
