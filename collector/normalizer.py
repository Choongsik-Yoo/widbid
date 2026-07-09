from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode


def _first(item: dict[str, Any], *keys: str, default=None):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def _number(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return None


def _timestamp(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y%m%d%H%M"):
        try:
            return datetime.strptime(text, fmt).isoformat()
        except ValueError:
            continue
    return text


def _bid_identity(item: dict[str, Any]) -> tuple[str, str]:
    raw_no = str(_first(item, "bidNtceNo", "bidNo", default="")).strip().upper()
    raw_no = re.sub(r"\s+", "", raw_no)
    match = re.fullmatch(r"(R\d{2}BK\d+)(?:-(\d{1,3}))?", raw_no)
    if match:
        bid_no = match.group(1)
        embedded_order = match.group(2)
    else:
        bid_no = re.sub(r"-\d{1,3}$", "", raw_no)
        embedded_order = None
    raw_order = _first(item, "bidNtceOrd", "bidOrd", default=embedded_order or "000")
    digits = re.sub(r"\D", "", str(raw_order))
    bid_order = (digits or "0").zfill(3)[-3:]
    return bid_no, bid_order


def build_detail_url(bid_no: str, bid_order: str) -> str:
    query = urlencode({"bidPbancNo": bid_no, "bidPbancOrd": bid_order})
    return f"https://www.g2b.go.kr/link/PNPE027_01/single/?{query}"


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    bid_no, bid_order = _bid_identity(item)
    title = str(_first(item, "bidNtceNm", "bidTitle", default="제목 없음")).strip()
    stable = {
        "bid_no": bid_no,
        "bid_order": bid_order,
        "title": title,
        "agency": _first(item, "ntceInsttNm", "agency"),
        "demand_agency": _first(item, "dminsttNm", "demandAgency"),
        "estimated_amount": _number(_first(item, "presmptPrce", "asignBdgtAmt")),
        "deadline_at": _timestamp(_first(item, "bidClseDt", "bidClseDate")),
    }
    content_hash = hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        **stable,
        "bid_type": _first(item, "bsnsDivNm", "bidType", default="물품"),
        "contract_method": _first(item, "cntrctCnclsMthdNm", "contractMethod"),
        "bid_method": _first(item, "bidMethdNm", "bidMethod", default="전자입찰"),
        "base_amount": _number(_first(item, "bssamt", "baseAmount")),
        "posted_at": _timestamp(_first(item, "bidNtceDt", "postedAt")),
        "opening_at": _timestamp(_first(item, "opengDt", "openingAt")),
        # API 응답에 상세 URL이 없거나 메인 URL만 오는 경우가 있어,
        # 공식 단건 링크 규칙으로 항상 정확한 공고 상세 주소를 생성합니다.
        "source_url": build_detail_url(bid_no, bid_order),
        "content_hash": content_hash,
        "raw_data": item,
        "status": "신규",
    }
