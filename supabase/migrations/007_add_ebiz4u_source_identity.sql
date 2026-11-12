-- Bidpage에서 먼저 수집된 eBiz4u 공고를 직접 eBiz4u 수집기와 같은
-- canonical identity로 재분류한다. 기존 Bidpage 출처 이력은 유지된다.
update public.bids
set canonical_source = 'ebiz4u',
    notice_agency = 'eBiz4u',
    source_url = 'https://www.ebiz4u.co.kr/bid/bidding.do'
      || '?cmd=viewPublic&subcmd=vwIndexOnPortal&rfqNo='
      || replace(bid_no, '-', '')
      || '&aspId=u.ebiz4u'
where canonical_source = 'bidpage'
  and bid_no ~ '^[A-Z][A-Z0-9]{4}-[0-9]{2}-[0-9]{8}-[0-9]{5}$';

comment on column public.bids.canonical_source is
  '중복 판별용 원 출처. 나라장터 재게시 공고는 g2b, eBiz4u 공고는 ebiz4u로 통합한다.';
