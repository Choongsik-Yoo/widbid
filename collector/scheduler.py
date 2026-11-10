from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    hour = int(os.getenv("COLLECT_AT_HOUR", "8"))
    if not 0 <= hour <= 23:
        raise ValueError("COLLECT_AT_HOUR는 0부터 23 사이여야 합니다.")

    marker = Path(os.getenv("STARTUP_MARKER", "/state/initial-run-complete"))
    if _enabled("RUN_ON_FIRST_START", True) and not marker.exists():
        return_code = run_collector()
        if return_code == 0:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()

    while True:
        target = next_run_at(hour=hour)
        log.info("다음 수집 예정: %s", target.isoformat())
        while True:
            remaining = (target - datetime.now(KST)).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 300))
        run_collector()


if __name__ == "__main__":
    main()
