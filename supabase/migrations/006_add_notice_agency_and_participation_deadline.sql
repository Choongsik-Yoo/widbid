alter table public.bids
  add column if not exists notice_agency text,
  add column if not exists participation_deadline_at timestamptz;

comment on column public.bids.notice_agency is
  '공고가 게시된 전자조달기관 또는 플랫폼(나라장터, ebiz4u 등)';
comment on column public.bids.participation_deadline_at is
  '입찰참가자격 등록 또는 참가신청 마감일시';

create or replace function public.withbid_kst_timestamp(value text)
returns timestamptz
language sql
immutable
strict
set search_path = public
as $$
  select case
    when btrim(value) ~ '^\d{14}$' then
      to_timestamp(btrim(value), 'YYYYMMDDHH24MISS')::timestamp at time zone 'Asia/Seoul'
    when btrim(value) ~ '^\d{12}$' then
      to_timestamp(btrim(value), 'YYYYMMDDHH24MI')::timestamp at time zone 'Asia/Seoul'
    else
      btrim(value)::timestamp at time zone 'Asia/Seoul'
  end
$$;

-- 기존 나라장터 원본에서 입찰참가자격등록마감일시를 복원합니다.
update public.bids
set notice_agency = case
      when canonical_source = 'g2b' then '나라장터'
      else coalesce(nullif(raw_data ->> 'notice_agency', ''), 'Bidpage')
    end,
    participation_deadline_at = case
      when nullif(raw_data ->> 'bidQlfctRgstDt', '') is not null
        then public.withbid_kst_timestamp(raw_data ->> 'bidQlfctRgstDt')
      when nullif(raw_data ->> 'participation_deadline_at', '') is not null
        then public.withbid_kst_timestamp(raw_data ->> 'participation_deadline_at')
      else participation_deadline_at
    end,
    updated_at = now()
where notice_agency is null
   or participation_deadline_at is null;

drop function public.withbid_kst_timestamp(text);

create index if not exists bids_participation_deadline_at_idx
  on public.bids (participation_deadline_at);
