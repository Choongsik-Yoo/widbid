from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


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


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    bid_no = str(_first(item, "bidNtceNo", "bidNo", default="")).strip()
    bid_order = str(_first(item, "bidNtceOrd", "bidOrd", default="000")).zfill(3)
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
        "source_url": _first(item, "bidNtceDtlUrl", "bidNtceUrl")
        or "https://www.g2b.go.kr/",
        "content_hash": content_hash,
        "raw_data": item,
        "status": "신규",
    }
