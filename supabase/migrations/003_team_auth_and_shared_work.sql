create table if not exists public.allowed_users (
  email text primary key check (email = lower(email)),
  display_name text,
  role text not null default 'member' check (role in ('admin', 'member')),
  is_active boolean not null default true,
  user_id uuid unique references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.allowed_users (email, display_name, role)
values ('csyoo22@gmail.com', '관리자', 'admin')
on conflict (email) do update set role = 'admin', is_active = true;

create or replace function public.current_user_email()
returns text language sql stable security definer set search_path = public
as $$ select lower(coalesce(auth.jwt() ->> 'email', '')) $$;

create or replace function public.is_allowed_user()
returns boolean language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.allowed_users
    where email = public.current_user_email() and is_active
  )
$$;

create or replace function public.is_team_admin()
returns boolean language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.allowed_users
    where email = public.current_user_email() and is_active and role = 'admin'
  )
$$;

create table if not exists public.team_bid_states (
  bid_id uuid primary key references public.bids(id) on delete cascade,
  is_saved boolean not null default false,
  status text not null default '신규' check (status in (
    '신규','검토중','참여가능','조건확인필요','대표승인필요',
    '제안/견적준비','투찰완료','낙찰','미선정','제외','보류'
  )),
  memo text not null default '',
  assigned_email text references public.allowed_users(email) on delete set null,
  updated_by text not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.team_bid_checklists (
  bid_id uuid not null references public.bids(id) on delete cascade,
  item_key text not null,
  item_label text not null,
  is_checked boolean not null default false,
  updated_by text not null,
  updated_at timestamptz not null default now(),
  primary key (bid_id, item_key)
);

create table if not exists public.team_activity_log (
  id bigint generated always as identity primary key,
  bid_id uuid references public.bids(id) on delete cascade,
  actor_email text not null,
  action text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.allowed_users enable row level security;
alter table public.team_bid_states enable row level security;
alter table public.team_bid_checklists enable row level security;
alter table public.team_activity_log enable row level security;

drop policy if exists "public read bids" on public.bids;
drop policy if exists "public read analyses" on public.bid_analyses;
drop policy if exists "public read keyword groups" on public.keyword_groups;
drop policy if exists "public read keywords" on public.keywords;

create policy "allowed users read bids" on public.bids
  for select to authenticated using (public.is_allowed_user());
create policy "allowed users read analyses" on public.bid_analyses
  for select to authenticated using (public.is_allowed_user());
create policy "allowed users read keyword groups" on public.keyword_groups
  for select to authenticated using (public.is_allowed_user());
create policy "allowed users read keywords" on public.keywords
  for select to authenticated using (public.is_allowed_user());

create policy "allowed users view team" on public.allowed_users
  for select to authenticated using (public.is_allowed_user());
create policy "admins manage allowed users" on public.allowed_users
  for all to authenticated using (public.is_team_admin()) with check (public.is_team_admin());
create policy "allowed users manage bid states" on public.team_bid_states
  for all to authenticated using (public.is_allowed_user()) with check (public.is_allowed_user());
create policy "allowed users manage checklists" on public.team_bid_checklists
  for all to authenticated using (public.is_allowed_user()) with check (public.is_allowed_user());
create policy "allowed users view activity" on public.team_activity_log
  for select to authenticated using (public.is_allowed_user());
create policy "allowed users add activity" on public.team_activity_log
  for insert to authenticated with check (
    public.is_allowed_user() and actor_email = public.current_user_email()
  );

grant select on public.allowed_users to authenticated;
grant insert, update, delete on public.allowed_users to authenticated;
grant select, insert, update, delete on public.team_bid_states, public.team_bid_checklists to authenticated;
grant select, insert on public.team_activity_log to authenticated;
grant usage, select on sequence public.team_activity_log_id_seq to authenticated;

create or replace function public.link_allowed_user()
returns trigger language plpgsql security definer set search_path = public
as $$
begin
  update public.allowed_users
  set user_id = new.id,
      display_name = coalesce(display_name, new.raw_user_meta_data ->> 'full_name'),
      updated_at = now()
  where email = lower(new.email) and is_active;
  return new;
end;
$$;

drop trigger if exists link_allowed_user_after_signup on auth.users;
create trigger link_allowed_user_after_signup
after insert or update of email on auth.users
for each row execute function public.link_allowed_user();

update public.allowed_users au
set user_id = u.id,
    display_name = coalesce(au.display_name, u.raw_user_meta_data ->> 'full_name'),
    updated_at = now()
from auth.users u
where au.email = lower(u.email);
