from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode


KST = timezone(timedelta(hours=9))
CONTENT_HASH_FIELDS = (
    "canonical_source", "bid_no", "bid_order", "title", "agency",
    "notice_agency", "demand_agency", "allocated_budget", "estimated_amount",
    "posted_at", "deadline_at", "opening_at", "participation_deadline_at",
)


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
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y%m%d%H%M%S",
        "%Y%m%d%H%M",
    ):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=KST).isoformat()
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST).isoformat()


def refresh_content_hash(item: dict[str, Any]) -> str:
    stable = {key: item.get(key) for key in CONTENT_HASH_FIELDS}
    return hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


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


def canonical_ebiz4u_bid_no(value: str) -> str | None:
    text = str(value or "").strip().upper()
    raw_match = re.fullmatch(r"([A-Z][A-Z0-9]{4})(\d{2})(\d{8})(\d{5})", text)
    if raw_match:
        return "-".join(raw_match.groups())
    display_match = re.fullmatch(
        r"([A-Z][A-Z0-9]{4})-(\d{2})-(\d{8})-(\d{5})", text
    )
    return "-".join(display_match.groups()) if display_match else None


def ebiz4u_rfq_no(value: str) -> str | None:
    canonical = canonical_ebiz4u_bid_no(value)
    return canonical.replace("-", "") if canonical else None


def build_ebiz4u_detail_url(rfq_no: str, asp_id: str = "u.ebiz4u") -> str:
    query = urlencode({
        "cmd": "viewPublic",
        "subcmd": "vwIndexOnPortal",
        "rfqNo": rfq_no,
        "aspId": asp_id,
    })
    return f"https://www.ebiz4u.co.kr/bid/bidding.do?{query}"


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    bid_no, bid_order = _bid_identity(item)
    title = str(_first(item, "bidNtceNm", "bidTitle", default="제목 없음")).strip()
    stable = {
        "bid_no": bid_no,
        "bid_order": bid_order,
        "title": title,
        "agency": _first(item, "ntceInsttNm", "agency"),
        "notice_agency": "나라장터",
        "demand_agency": _first(item, "dminsttNm", "demandAgency"),
        "allocated_budget": _number(_first(item, "asignBdgtAmt", "allocatedBudget")),
        "estimated_amount": _number(_first(item, "presmptPrce", "estimatedAmount")),
        "posted_at": _timestamp(_first(item, "bidNtceDt", "postedAt")),
        "deadline_at": _timestamp(_first(item, "bidClseDt", "bidClseDate")),
        "opening_at": _timestamp(_first(item, "opengDt", "openingAt")),
        "participation_deadline_at": _timestamp(
            _first(item, "bidQlfctRgstDt", "participationDeadlineAt")
        ),
    }
    content_hash = hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        **stable,
        "canonical_source": "g2b",
        "bid_type": _first(item, "bsnsDivNm", "bidType", default="물품"),
        "contract_method": _first(item, "cntrctCnclsMthdNm", "contractMethod"),
        "bid_method": _first(item, "bidMethdNm", "bidMethod", default="전자입찰"),
        "base_amount": _number(_first(item, "bssamt", "baseAmount")),
        # API 응답에 상세 URL이 없거나 메인 URL만 오는 경우가 있어,
        # 공식 단건 링크 규칙으로 항상 정확한 공고 상세 주소를 생성합니다.
        "source_url": build_detail_url(bid_no, bid_order),
        "content_hash": content_hash,
        "raw_data": item,
        "status": "신규",
        "source_record": {
            "source_system": "g2b",
            "source_bid_id": bid_no,
            "source_bid_order": bid_order,
            "source_url": build_detail_url(bid_no, bid_order),
            "raw_data": item,
        },
    }


def normalize_bidpage(item: dict[str, Any]) -> dict[str, Any]:
    official_no = str(item.get("official_bid_no") or "").strip().upper()
    official_order = str(item.get("official_bid_order") or "000")
    is_g2b = bool(re.fullmatch(r"R\d{2}BK\d+", official_no))
    ebiz4u_bid_no = canonical_ebiz4u_bid_no(official_no)

    if is_g2b:
        bid_no, bid_order = _bid_identity(
            {"bidNtceNo": official_no, "bidNtceOrd": official_order}
        )
        canonical_source = "g2b"
        source_url = build_detail_url(bid_no, bid_order)
    elif ebiz4u_bid_no:
        bid_no = ebiz4u_bid_no
        bid_order = "000"
        canonical_source = "ebiz4u"
        source_url = build_ebiz4u_detail_url(ebiz4u_rfq_no(bid_no) or "")
    else:
        bid_no = official_no or str(item.get("bidpage_bid_no") or "").strip()
        bid_order = re.sub(r"\D", "", official_order).zfill(3)[-3:]
        canonical_source = "bidpage"
        source_url = item.get("original_url") or item.get("detail_url")

    if not bid_no:
        raise ValueError("Bidpage 공고 식별번호가 없습니다.")

    title = str(item.get("title") or "제목 없음").strip()
    stable = {
        "canonical_source": canonical_source,
        "bid_no": bid_no,
        "bid_order": bid_order,
        "title": title,
        "agency": item.get("agency"),
        "notice_agency": item.get("notice_agency") or (
            "나라장터" if is_g2b else "Bidpage"
        ),
        "demand_agency": item.get("demand_agency"),
        "allocated_budget": _number(item.get("allocated_budget")),
        "estimated_amount": _number(item.get("estimated_amount")),
        "posted_at": _timestamp(item.get("posted_at")),
        "deadline_at": _timestamp(item.get("deadline_at")),
        "opening_at": _timestamp(item.get("opening_at")),
        "participation_deadline_at": _timestamp(
            item.get("participation_deadline_at")
        ),
    }
    content_hash = hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    source_bid_id = str(item.get("bidpage_bid_no") or bid_no)
    source_bid_order = str(item.get("bidpage_bid_seq") or "0")
    return {
        **stable,
        "bid_type": item.get("bid_type") or "물품",
        "contract_method": item.get("contract_method"),
        "bid_method": item.get("bid_method"),
        "base_amount": _number(item.get("base_amount")),
        "source_url": source_url,
        "content_hash": content_hash,
        "raw_data": item,
        "status": "신규",
        "source_record": {
            "source_system": "bidpage",
            "source_bid_id": source_bid_id,
            "source_bid_order": source_bid_order,
            "source_url": source_url,
            "raw_data": item,
        },
    }


def normalize_ebiz4u(item: dict[str, Any]) -> dict[str, Any]:
    rfq_no = str(item.get("rfq_no") or "").strip().upper()
    bid_no = canonical_ebiz4u_bid_no(rfq_no)
    if not bid_no:
        raise ValueError("eBiz4u 공고 식별번호 형식이 올바르지 않습니다.")
    title = str(item.get("title") or "제목 없음").strip()
    stable = {
        "canonical_source": "ebiz4u",
        "bid_no": bid_no,
        "bid_order": "000",
        "title": title,
        "agency": item.get("agency"),
        "notice_agency": "eBiz4u",
        "demand_agency": item.get("demand_agency") or item.get("agency"),
        "allocated_budget": _number(item.get("allocated_budget")),
        "estimated_amount": _number(item.get("estimated_amount")),
        "posted_at": _timestamp(item.get("posted_at")),
        "deadline_at": _timestamp(item.get("deadline_at")),
        "opening_at": _timestamp(item.get("opening_at")),
        "participation_deadline_at": _timestamp(
            item.get("participation_deadline_at")
        ),
    }
    content_hash = hashlib.sha256(
        json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    detail_url = item.get("detail_url") or build_ebiz4u_detail_url(
        rfq_no, str(item.get("asp_id") or "u.ebiz4u")
    )
    return {
        **stable,
        "bid_type": item.get("bid_type") or "물품",
        "contract_method": item.get("contract_method"),
        "bid_method": "전자입찰",
        "base_amount": _number(item.get("base_amount")),
        "source_url": detail_url,
        "content_hash": content_hash,
        "raw_data": item,
        "status": "신규",
        "source_record": {
            "source_system": "ebiz4u",
            "source_bid_id": rfq_no,
            "source_bid_order": "0",
            "source_url": detail_url,
            "raw_data": item,
        },
    }
