alter table public.bids
  add column if not exists allocated_budget bigint;

comment on column public.bids.allocated_budget is
  '나라장터 입찰공고정보서비스 asignBdgtAmt(배정예산)';

create or replace function public.g2b_kst_timestamp(value text)
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

-- 기존 행은 수집 당시 보존한 API 원본에서 다시 계산합니다.
-- 이미 timestamptz에 저장된 잘못된 값에서 9시간을 빼는 방식보다 원본 복원이 안전합니다.
update public.bids
set allocated_budget = case
      when nullif(raw_data ->> 'asignBdgtAmt', '') ~ '^\d+(\.\d+)?$'
        then (raw_data ->> 'asignBdgtAmt')::numeric::bigint
      else null
    end,
    posted_at = case
      when nullif(raw_data ->> 'bidNtceDt', '') is not null
        then public.g2b_kst_timestamp(raw_data ->> 'bidNtceDt')
      else posted_at
    end,
    deadline_at = case
      when nullif(raw_data ->> 'bidClseDt', '') is not null
        then public.g2b_kst_timestamp(raw_data ->> 'bidClseDt')
      else deadline_at
    end,
    opening_at = case
      when nullif(raw_data ->> 'opengDt', '') is not null
        then public.g2b_kst_timestamp(raw_data ->> 'opengDt')
      else opening_at
    end,
    updated_at = now()
where raw_data is not null;

drop function public.g2b_kst_timestamp(text);
