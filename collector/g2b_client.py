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

    @staticmethod
    def _items(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        response = payload.get("response", {})
        header = response.get("header", {})
        result_code = str(header.get("resultCode") or "00")
        if result_code not in {"00", "0"}:
            raise RuntimeError(
                f"나라장터 API 오류 {result_code}: {header.get('resultMsg') or '알 수 없음'}"
            )
        body = response.get("body", {})
        items = body.get("items") or []
        if isinstance(items, dict):
            items = items.get("item") or []
        if isinstance(items, dict):
            items = [items]
        return items, int(body.get("totalCount") or len(items))

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
            items, total = self._items(response.json())
            results.extend(items)
            log.info("나라장터 %s페이지: %s건 / 전체 %s건", page, len(items), total)
            if not items or len(results) >= total:
                break
            page += 1
        return results

    def participation_regions(
        self, start_at: datetime, end_at: datetime
    ) -> dict[tuple[str, str], list[str]]:
        """공식 참가가능지역정보 API를 기간 단위로 조회합니다."""
        page = 1
        fetched = 0
        results: dict[tuple[str, str], list[str]] = {}
        while True:
            response = self.session.get(
                self.config.g2b_region_url,
                params={
                    "serviceKey": self.config.data_api_key,
                    "type": "json",
                    "numOfRows": self.config.page_size,
                    "pageNo": page,
                    "inqryDiv": "1",
                    "inqryBgnDt": start_at.strftime("%Y%m%d%H%M"),
                    "inqryEndDt": end_at.strftime("%Y%m%d%H%M"),
                },
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            items, total = self._items(response.json())
            fetched += len(items)
            for item in items:
                bid_no = str(item.get("bidNtceNo") or "").strip().upper()
                order = str(item.get("bidNtceOrd") or "000").zfill(3)[-3:]
                region = str(
                    item.get("prtcptPsblRgnNm")
                    or item.get("prtcptLmtRgnNm")
                    or ""
                ).strip()
                if bid_no and region:
                    regions = results.setdefault((bid_no, order), [])
                    if region not in regions:
                        regions.append(region)
            log.info(
                "나라장터 참가가능지역 %s페이지: %s건 / 전체 %s건",
                page, len(items), total,
            )
            if not items or fetched >= total:
                break
            page += 1
        return results
