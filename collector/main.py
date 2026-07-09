from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from config import Config
from g2b_client import G2BClient
from keyword_matcher import DEFAULT_KEYWORDS, matched_keywords
from normalizer import normalize
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
    client = G2BClient(config)
    now = datetime.now(KST)
    run_id = repository.create_run(now.isoformat())
    try:
        keywords = repository.active_keywords() or DEFAULT_KEYWORDS
        # API 호출량을 줄이기 위해 전체 신규 공고를 한 번 수집한 뒤 로컬 매칭합니다.
        raw_items = client.search(now - timedelta(days=2), now)
        normalized = [normalize(item) for item in raw_items]
        matched = []
        for bid in normalized:
            matches = matched_keywords(bid, keywords)
            if matches:
                bid["matched_keywords"] = matches
                matched.append(bid)
        saved_bids = repository.upsert_bids(matched)
        analyses = [
            {"bid_id": saved["id"], **analyze_bid(saved)}
            for saved in saved_bids
        ]
        repository.upsert_analyses(analyses)
        repository.finish_run(
            run_id,
            status="success",
            finished_at=datetime.now(KST).isoformat(),
            fetched_count=len(raw_items),
            matched_count=len(matched),
            analyzed_count=len(analyses),
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
