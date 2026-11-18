from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
log = logging.getLogger(__name__)


def _enabled(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def next_run_at(now: datetime | None = None, hour: int = 8) -> datetime:
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current = current.astimezone(KST)
    target = current.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= current:
        target += timedelta(days=1)
    return target


def read_last_success(marker: Path) -> date | None:
    if not marker.exists():
        return None
    try:
        return date.fromisoformat(marker.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        log.warning("마지막 수집일 기록을 읽을 수 없습니다: %s", marker)
        return None


def should_catch_up(
    now: datetime, last_success: date | None, hour: int = 8
) -> bool:
    current = now if now.tzinfo else now.replace(tzinfo=KST)
    current = current.astimezone(KST)
    return current.hour >= hour and (
        last_success is None or last_success < current.date()
    )


def record_success(marker: Path, completed_at: datetime | None = None) -> None:
    current = completed_at or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    marker.parent.mkdir(parents=True, exist_ok=True)
    temporary = marker.with_suffix(f"{marker.suffix}.tmp")
    temporary.write_text(
        current.astimezone(KST).date().isoformat(), encoding="utf-8"
    )
    temporary.replace(marker)


def run_collector() -> int:
    log.info("WithBid 수집을 시작합니다.")
    completed = subprocess.run(
        [sys.executable, "main.py"],
        cwd=Path(__file__).resolve().parent,
        check=False,
    )
    if completed.returncode:
        log.error("WithBid 수집 실패 (종료 코드 %s)", completed.returncode)
    else:
        log.info("WithBid 수집 완료")
    return completed.returncode


def run_and_record(marker: Path) -> int:
    return_code = run_collector()
    if return_code == 0:
        record_success(marker)
    return return_code


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    hour = int(os.getenv("COLLECT_AT_HOUR", "8"))
    if not 0 <= hour <= 23:
        raise ValueError("COLLECT_AT_HOUR는 0부터 23 사이여야 합니다.")
    retry_minutes = int(os.getenv("RETRY_AFTER_MINUTES", "30"))
    if retry_minutes < 1:
        raise ValueError("RETRY_AFTER_MINUTES는 1 이상이어야 합니다.")

    marker = Path(
        os.getenv("LAST_SUCCESS_MARKER", "/state/last-successful-run-date")
    )
    legacy_marker = Path(
        os.getenv("STARTUP_MARKER", "/state/initial-run-complete")
    )
    now = datetime.now(KST)
    last_success = read_last_success(marker)
    first_start = (
        _enabled("RUN_ON_FIRST_START", True)
        and last_success is None
        and not legacy_marker.exists()
    )
    retry_at: datetime | None = None
    if first_start or should_catch_up(now, last_success, hour):
        reason = "최초 실행" if first_start else "당일 미수집 보충"
        log.info("%s 수집을 시작합니다.", reason)
        if run_and_record(marker) == 0:
            legacy_marker.parent.mkdir(parents=True, exist_ok=True)
            legacy_marker.touch(exist_ok=True)
        else:
            retry_at = datetime.now(KST) + timedelta(minutes=retry_minutes)

    while True:
        target = retry_at or next_run_at(hour=hour)
        log.info("다음 수집 예정: %s", target.isoformat())
        while True:
            remaining = (target - datetime.now(KST)).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 300))
        if run_and_record(marker) == 0:
            retry_at = None
        else:
            retry_at = datetime.now(KST) + timedelta(minutes=retry_minutes)


if __name__ == "__main__":
    main()
