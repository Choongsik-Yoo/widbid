from __future__ import annotations

from typing import Any


DEFAULT_KEYWORDS = [
    "컴퓨터", "PC", "데스크톱", "노트북", "랩탑", "서버", "SERVER",
    "GPU 서버", "워크스테이션", "전산장비", "전산기기", "전산설비",
    "네트워크", "스토리지", "NAS", "SAN", "방화벽", "스위치",
    "모니터", "프린터", "스캐너", "UPS", "전자칠판", "LED 전광판",
]


def matched_keywords(bid: dict[str, Any], keywords: list[str]) -> list[str]:
    raw = bid.get("raw_data") or {}
    text = " ".join(
        str(value) for value in [
            bid.get("title"), bid.get("agency"), bid.get("demand_agency"),
            raw.get("bidNtceNm"), raw.get("prdctClsfcNoNm"),
        ] if value
    ).casefold()
    return [keyword for keyword in keywords if keyword.casefold() in text]
