from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import Config
from normalizer import build_ebiz4u_detail_url


log = logging.getLogger(__name__)


def _text(node) -> str:
    return " ".join(node.stripped_strings) if node else ""


def _date(value: str) -> str | None:
    text = re.sub(r"\s+", " ", value or "").strip()
    match = re.search(
        r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})"
        r"(?:\s*(\d{1,2}):(\d{2})(?::(\d{2}))?)?",
        text,
    )
    if not match:
        return None
    year, month, day, hour, minute, second = match.groups()
    return (
        f"{int(year):04d}-{int(month):02d}-{int(day):02d} "
        f"{int(hour or 0):02d}:{int(minute or 0):02d}:{int(second or 0):02d}"
    )


def _bid_type(title: str) -> str:
    if re.search(r"(?:시설|전기|통신|소방|건축|토목|조경)\s*공사|\[공사\]", title):
        return "공사"
    if re.search(r"용역|컨설팅|유지보수|임대", title):
        return "용역"
    return "물품"


class Ebiz4uClient:
    list_path = "/bid/bidding.do?cmd=listPublic&subcmd=doPortalList"

    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (compatible; WithBidCollector/1.0; "
                "+https://github.com/Choongsik-Yoo/widbid)"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9",
        })

    @property
    def list_url(self) -> str:
        return f"{self.config.ebiz4u_base_url}{self.list_path}"

    @staticmethod
    def _decode(response: requests.Response) -> str:
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def parse_list(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        pattern = re.compile(
            r"doView\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]"
        )
        for link in soup.select('a[href*="doView("]'):
            match = pattern.search(link.get("href", ""))
            if not match:
                continue
            rfq_no, asp_id = match.groups()
            if rfq_no in seen:
                continue
            seen.add(rfq_no)
            row = link.find_parent("tr")
            cells = row.find_all("td", recursive=False) if row else []
            if len(cells) < 5:
                continue
            organization_node = link.select_one("span.subject")
            organization = _text(organization_node)
            title = _text(link)
            if organization and title.startswith(organization):
                title = title[len(organization):].strip()
            results.append({
                "rfq_no": rfq_no,
                "asp_id": asp_id,
                "title": title or _text(link),
                "agency": organization,
                "demand_agency": organization,
                "notice_agency": "eBiz4u",
                "manager": _text(cells[1]),
                "posted_at": _date(_text(cells[2])),
                "deadline_at": _date(_text(cells[3])),
                "status_text": _text(cells[4]),
                "bid_type": _bid_type(title),
                "detail_url": build_ebiz4u_detail_url(rfq_no, asp_id),
            })
        return results

    @staticmethod
    def parse_detail(html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        fields: dict[str, str] = {}
        for row in soup.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            for index in range(0, len(cells) - 1, 2):
                key = re.sub(r"\s+", "", _text(cells[index]))
                value = _text(cells[index + 1])
                if key and value:
                    fields[key] = value

        def field(*labels: str) -> str:
            for label in labels:
                normalized = re.sub(r"\s+", "", label)
                for key, value in fields.items():
                    if key == normalized or normalized in key:
                        return value
            return ""

        item_rows: list[dict[str, str]] = []
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            header_index = next((
                index for index, row in enumerate(rows)
                if any(
                    "물품명" in re.sub(r"\s+", "", _text(node))
                    for node in row.find_all(["th", "td"], recursive=False)
                )
            ), None)
            if header_index is None:
                continue
            for row in rows[header_index + 1:]:
                cells = row.find_all("td", recursive=False)
                if len(cells) >= 3:
                    item_rows.append({
                        "name": _text(cells[0]),
                        "model": _text(cells[1]),
                        "quantity": _text(cells[2]),
                        "delivery_due": _text(cells[3]) if len(cells) > 3 else "",
                        "delivery_place": _text(cells[4]) if len(cells) > 4 else "",
                    })

        invitation_no = field("입찰초청서번호")
        return {
            "rfq_no": invitation_no,
            "title": field("입찰명"),
            "agency": field("구매사"),
            "demand_agency": field("구매사"),
            "posted_at": _date(field("게시일시")),
            "deadline_at": _date(field("입찰마감일시")),
            "region_limit": field("참가가능지역", "참가지역", "지역제한") or None,
            "contract_method": " / ".join(filter(None, (
                field("입찰종류1"), field("입찰종류2")
            ))),
            "notice_text": field("비고"),
            "items": item_rows,
        }

    def enrich_details(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            try:
                response = self.session.get(
                    item["detail_url"], timeout=self.config.request_timeout
                )
                response.raise_for_status()
                details = self.parse_detail(self._decode(response))
                enriched.append({
                    **item,
                    **{key: value for key, value in details.items() if value},
                })
            except requests.RequestException as exc:
                log.warning("eBiz4u 상세정보 수집 실패 (%s): %s", item["rfq_no"], exc)
                enriched.append(item)
            if index + 1 < len(items):
                time.sleep(0.2)
        return enriched

    def search(self, start_at: datetime, end_at: datetime) -> list[dict[str, Any]]:
        del end_at  # 공개 목록은 진행 중 공고를 최신 게시순으로 제공합니다.
        results: dict[str, dict[str, Any]] = {}
        for page in range(1, self.config.ebiz4u_max_pages + 1):
            response = self.session.post(
                self.list_url,
                data={
                    "page": str(page),
                    "cmd": "listPublic",
                    "subcmd": "doPortalList",
                    "srchAspUrl": "",
                    "srchRfqNm": "",
                    "srchOrgNm": "",
                    "srchFrDt": "",
                    "srchToDt": "",
                },
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            html = self._decode(response)
            page_results = self.parse_list(html)
            recent = []
            for item in page_results:
                posted_at = item.get("posted_at")
                if posted_at and datetime.fromisoformat(posted_at) >= start_at.replace(tzinfo=None):
                    results[item["rfq_no"]] = item
                    recent.append(item)
            log.info("eBiz4u 공개공고 %s페이지: %s건", page, len(page_results))
            if not page_results or (not recent and all(item.get("posted_at") for item in page_results)):
                break
            if not re.search(rf"gotoLink\(['\"]?{page + 1}['\"]?\)", html):
                break
        collected = list(results.values())
        log.info("eBiz4u 공개공고 %s건 수집", len(collected))
        return collected
