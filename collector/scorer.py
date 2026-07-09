from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def analyze_bid(bid: dict[str, Any]) -> dict[str, Any]:
    """Calculate a conservative baseline score from public API fields."""

    keywords = bid.get("matched_keywords") or []
    amount = bid.get("estimated_amount") or bid.get("base_amount")
    deadline = _parse_datetime(bid.get("deadline_at"))
    now = datetime.now(deadline.tzinfo if deadline else timezone.utc)
    days_left = (deadline - now).days if deadline else None

    product = min(25, 15 + len(keywords) * 5) if keywords else 0
    if amount is None:
        amount_score = 5
    elif 10_000_000 <= amount <= 500_000_000:
        amount_score = 15
    elif 1_000_000 <= amount <= 1_000_000_000:
        amount_score = 10
    else:
        amount_score = 5

    certification = 10
    region = 10
    delivery = 10 if days_left is not None and days_left >= 7 else 5
    performance = 5

    risks: list[str] = []
    if amount is None:
        risks.append("예산 금액 확인 필요")
    if days_left is None:
        risks.append("입찰 마감일 확인 필요")
    elif days_left < 3:
        risks.append("입찰 마감 임박")
    risks.append("인증·실적 조건은 공고 원문 및 첨부파일 확인 필요")

    risk = max(0, 10 - max(0, len(risks) - 1) * 3)
    breakdown = [
        product,
        amount_score,
        certification,
        region,
        delivery,
        performance,
        risk,
    ]
    score = max(0, min(100, sum(breakdown)))
    keyword_text = ", ".join(keywords[:5]) or "등록 키워드"
    analyzed_at = datetime.now(timezone.utc).isoformat()

    return {
        "summary": (
            f"공고명에서 {keyword_text} 관련성이 확인되었습니다. "
            "공개 API 기본정보를 이용한 1차 자동평가이며, 인증·실적 조건은 "
            "나라장터 원문과 첨부파일을 확인해야 합니다."
        ),
        "required_certifications": [],
        "required_documents": [],
        "qualification_requirements": [],
        "region_limit": "전국",
        "risk_factors": risks,
        "score_breakdown": breakdown,
        "fit_score": score,
        "recommendation": (
            "우선 검토" if score >= 70 else "조건 확인 필요" if score >= 50 else "제외 검토"
        ),
        "confidence": 0.55,
        "ai_model": "rule-baseline-v1",
        "analyzed_at": analyzed_at,
        "updated_at": analyzed_at,
    }
