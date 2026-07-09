from __future__ import annotations

import logging
from typing import Any

import requests

from config import Config

log = logging.getLogger(__name__)


class SupabaseRepository:
    def __init__(self, config: Config) -> None:
        self.base_url = f"{config.supabase_url}/rest/v1"
        self.headers = {
            "apikey": config.supabase_service_key,
            "Authorization": f"Bearer {config.supabase_service_key}",
            "Content-Type": "application/json",
        }

    def active_keywords(self) -> list[str]:
        response = requests.get(
            f"{self.base_url}/keywords",
            params={"select": "keyword", "is_active": "eq.true"},
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return [row["keyword"] for row in response.json()]

    def create_run(self, started_at: str) -> str:
        response = requests.post(
            f"{self.base_url}/collection_runs",
            headers={**self.headers, "Prefer": "return=representation"},
            json={"started_at": started_at, "status": "running"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()[0]["id"]

    def finish_run(self, run_id: str, **values: Any) -> None:
        response = requests.patch(
            f"{self.base_url}/collection_runs",
            params={"id": f"eq.{run_id}"},
            headers=self.headers,
            json=values,
            timeout=30,
        )
        response.raise_for_status()

    def upsert_bids(self, bids: list[dict[str, Any]]) -> None:
        if not bids:
            return
        response = requests.post(
            f"{self.base_url}/bids",
            params={"on_conflict": "bid_no,bid_order,bid_type"},
            headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
            json=bids,
            timeout=60,
        )
        response.raise_for_status()
        log.info("Supabase에 %s건 upsert 완료", len(bids))
