from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

from config import Config

log = logging.getLogger(__name__)


class G2BClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()

    def search(
        self,
        start_at: datetime,
        end_at: datetime,
        keyword: str | None = None,
    ) -> list[dict[str, Any]]:
        page = 1
        results: list[dict[str, Any]] = []
        while True:
            params = {
                "serviceKey": self.config.data_api_key,
                "type": "json",
                "numOfRows": self.config.page_size,
                "pageNo": page,
                "inqryDiv": "1",
                "inqryBgnDt": start_at.strftime("%Y%m%d%H%M"),
                "inqryEndDt": end_at.strftime("%Y%m%d%H%M"),
            }
            if keyword:
                params["bidNtceNm"] = keyword
            response = self.session.get(
                self.config.g2b_base_url,
                params=params,
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            payload = response.json()
            body = payload.get("response", {}).get("body", {})
            items = body.get("items") or []
            if isinstance(items, dict):
                items = items.get("item") or []
            if isinstance(items, dict):
                items = [items]
            results.extend(items)
            total = int(body.get("totalCount") or len(results))
            log.info("나라장터 %s페이지: %s건 / 전체 %s건", page, len(items), total)
            if not items or len(results) >= total:
                break
            page += 1
        return results
