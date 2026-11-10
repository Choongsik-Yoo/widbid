from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from config import Config
from bidpage_client import BidpageClient
from g2b_client import G2BClient
from keyword_matcher import DEFAULT_KEYWORDS, matched_keywords
from normalizer import normalize, normalize_bidpage
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
        normalized = [normalize(item) for item in raw_items]
        bidpage_error: str | None = None
        if config.bidpage_enabled:
            try:
                bidpage_client = BidpageClient(config)
                bidpage_items = bidpage_client.search(start_at, now)
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
                bidpage_error = f"Bidpage 수집 실패: {exc}"[:2000]
                logging.getLogger(__name__).exception(bidpage_error)

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
                else:
                    bid["source_records"] = [bid.pop("source_record")]
                    matched_by_identity[identity] = bid

        matched = list(matched_by_identity.values())
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
            status="partial" if bidpage_error else "success",
            finished_at=datetime.now(KST).isoformat(),
            fetched_count=len(raw_items),
            matched_count=len(matched),
            analyzed_count=len(analyses),
            error_message=bidpage_error,
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
