-- Existing production projects: explicit Data API privileges.
-- Safe to run repeatedly.

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
