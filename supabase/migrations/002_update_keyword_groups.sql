insert into public.keyword_groups (group_name)
values ('기타')
on conflict (group_name) do nothing;

insert into public.keywords (group_id, keyword)
select g.id, keyword
from public.keyword_groups g
cross join unnest(array['모니터']) keyword
where g.group_name = 'PC·컴퓨터'
on conflict (group_id, keyword, match_type) do nothing;

insert into public.keywords (group_id, keyword)
select g.id, keyword
from public.keyword_groups g
cross join unnest(array['소프트웨어', '렌탈', '리스']) keyword
where g.group_name = '기타'
on conflict (group_id, keyword, match_type) do nothing;
