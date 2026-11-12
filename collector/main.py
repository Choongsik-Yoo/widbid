from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from config import Config
from bidpage_client import BidpageClient
from ebiz4u_client import Ebiz4uClient
from g2b_client import G2BClient
from keyword_matcher import DEFAULT_KEYWORDS, matched_keywords
from normalizer import (
    normalize, normalize_bidpage, normalize_ebiz4u, refresh_content_hash,
)
from scorer import analyze_bid
from supabase_repository import SupabaseRepository

KST = timezone(timedelta(hours=9))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = Config.from_env()
    repository = SupabaseRepository(config)
    g2b_client = G2BClient(config)
    now = datetime.now(KST)
    run_id = repository.create_run(now.isoformat())
    try:
        keywords = repository.active_keywords() or DEFAULT_KEYWORDS
        # API 호출량을 줄이기 위해 전체 신규 공고를 한 번 수집한 뒤 로컬 매칭합니다.
        start_at = now - timedelta(days=2)
        raw_items = g2b_client.search(start_at, now)
        source_errors: list[str] = []
        try:
            region_map = g2b_client.participation_regions(start_at, now)
            for item in raw_items:
                identity = normalize(item)
                item["participation_regions"] = region_map.get(
                    (identity["bid_no"], identity["bid_order"]), []
                )
        except Exception as exc:
            # 지역 보조 API 장애 시 공고 자체의 수집은 유지하되 실행 결과를
            # 부분 성공으로 기록하여 '전국'으로 잘못 단정하지 않습니다.
            error = f"나라장터 참가가능지역 수집 실패: {exc}"[:1000]
            source_errors.append(error)
            logging.getLogger(__name__).exception(error)
        normalized = [normalize(item) for item in raw_items]
        if config.ebiz4u_enabled:
            try:
                ebiz4u_client = Ebiz4uClient(config)
                ebiz4u_items = ebiz4u_client.search(start_at, now)
                detail_targets = [
                    item for item in ebiz4u_items
                    if matched_keywords(normalize_ebiz4u(item), keywords)
                ]
                ebiz4u_items = ebiz4u_client.enrich_details(detail_targets)
                raw_items.extend(ebiz4u_items)
                normalized.extend(normalize_ebiz4u(item) for item in ebiz4u_items)
            except Exception as exc:
                error = f"eBiz4u 수집 실패: {exc}"[:1000]
                source_errors.append(error)
                logging.getLogger(__name__).exception(error)
        if config.bidpage_enabled:
            try:
                bidpage_client = BidpageClient(config)
                bidpage_items = bidpage_client.search(start_at, now)
                # 방어적으로 한 번 더 제외하여 eBiz4u 공고가 Bidpage 출처로
                # 저장되는 일을 막습니다. eBiz4u는 전용 수집기만 담당합니다.
                bidpage_items = [
                    item for item in bidpage_items
                    if "ebiz4u" not in str(item.get("notice_agency") or "").lower()
                    and not normalize_bidpage(item)["canonical_source"] == "ebiz4u"
                ]
                # 목록에서 키워드가 맞는 공고만 상세 조회하여 발주기관과
                # 참가신청마감일을 정확히 보강하고 사이트 부하를 줄입니다.
                detail_targets = [
                    item for item in bidpage_items
                    if matched_keywords(normalize_bidpage(item), keywords)
                ]
                bidpage_items = bidpage_client.enrich_details(detail_targets)
                raw_items.extend(bidpage_items)
                normalized.extend(normalize_bidpage(item) for item in bidpage_items)
            except Exception as exc:
                # 보조 출처 장애가 나라장터 수집까지 중단시키지 않도록 부분 성공 처리합니다.
                error = f"Bidpage 수집 실패: {exc}"[:1000]
                source_errors.append(error)
                logging.getLogger(__name__).exception(error)

        matched_by_identity: dict[tuple[str, str, str, str], dict] = {}
        for bid in normalized:
            matches = matched_keywords(bid, keywords)
            if matches:
                bid["matched_keywords"] = matches
                identity = (
                    bid["canonical_source"], bid["bid_no"],
                    bid["bid_order"], bid["bid_type"],
                )
                existing = matched_by_identity.get(identity)
                if existing:
                    existing["matched_keywords"] = sorted(set(
                        [*existing["matched_keywords"], *matches]
                    ))
                    existing["source_records"].append(bid["source_record"])
                    for field in (
                        "agency", "demand_agency", "allocated_budget",
                        "estimated_amount", "posted_at", "deadline_at",
                        "opening_at", "participation_deadline_at",
                        "contract_method", "bid_method", "base_amount",
                    ):
                        if not existing.get(field) and bid.get(field):
                            existing[field] = bid[field]
                else:
                    bid["source_records"] = [bid.pop("source_record")]
                    matched_by_identity[identity] = bid

        matched = list(matched_by_identity.values())
        for bid in matched:
            bid["content_hash"] = refresh_content_hash(bid)
        payloads = [
            {key: value for key, value in bid.items() if key != "source_records"}
            for bid in matched
        ]
        saved_bids = repository.upsert_bids(payloads)
        saved_by_identity = {
            (
                bid["canonical_source"], bid["bid_no"],
                bid["bid_order"], bid["bid_type"],
            ): bid["id"]
            for bid in saved_bids
        }
        sources_by_identity = {}
        for identity, bid in matched_by_identity.items():
            bid_id = saved_by_identity.get(identity)
            if not bid_id:
                continue
            for source in bid["source_records"]:
                source_identity = (
                    source["source_system"], source["source_bid_id"],
                    source["source_bid_order"],
                )
                sources_by_identity[source_identity] = {"bid_id": bid_id, **source}
        repository.upsert_bid_sources(list(sources_by_identity.values()))
        analysis_targets = {
            bid["id"]: bid
            for bid in [*saved_bids, *repository.bids_without_analysis()]
        }
        analyses = [
            {"bid_id": bid["id"], **analyze_bid(bid)}
            for bid in analysis_targets.values()
        ]
        repository.upsert_analyses(analyses)
        repository.finish_run(
            run_id,
            status="partial" if source_errors else "success",
            finished_at=datetime.now(KST).isoformat(),
            fetched_count=len(raw_items),
            matched_count=len(matched),
            analyzed_count=len(analyses),
            error_message="; ".join(source_errors)[:2000] or None,
        )
    except Exception as exc:
        repository.finish_run(
            run_id,
            status="failed",
            finished_at=datetime.now(KST).isoformat(),
            error_message=str(exc)[:2000],
        )
        raise


if __name__ == "__main__":
    main()
