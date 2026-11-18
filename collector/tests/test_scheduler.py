from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scheduler import next_run_at, read_last_success, record_success, should_catch_up


KST = timezone(timedelta(hours=9))


class SchedulerTests(unittest.TestCase):
    def test_schedules_same_day_before_eight(self):
        now = datetime(2026, 11, 10, 7, 30, tzinfo=KST)
        self.assertEqual(
            next_run_at(now),
            datetime(2026, 11, 10, 8, 0, tzinfo=KST),
        )

    def test_schedules_next_day_at_or_after_eight(self):
        now = datetime(2026, 11, 10, 8, 0, tzinfo=KST)
        self.assertEqual(
            next_run_at(now),
            datetime(2026, 11, 11, 8, 0, tzinfo=KST),
        )

    def test_catches_up_when_started_after_eight_without_today_run(self):
        now = datetime(2026, 11, 18, 10, 30, tzinfo=KST)
        self.assertTrue(should_catch_up(now, date(2026, 11, 17), hour=8))

    def test_does_not_catch_up_before_scheduled_hour(self):
        now = datetime(2026, 11, 18, 7, 30, tzinfo=KST)
        self.assertFalse(should_catch_up(now, date(2026, 11, 17), hour=8))

    def test_does_not_repeat_after_today_run(self):
        now = datetime(2026, 11, 18, 15, 0, tzinfo=KST)
        self.assertFalse(should_catch_up(now, date(2026, 11, 18), hour=8))

    def test_missing_record_catches_up_after_eight(self):
        now = datetime(2026, 11, 18, 9, 0, tzinfo=KST)
        self.assertTrue(should_catch_up(now, None, hour=8))

    def test_records_success_date_in_persistent_marker(self):
        with TemporaryDirectory() as directory:
            marker = Path(directory) / "last-successful-run-date"
            record_success(marker, datetime(2026, 11, 18, 8, 5, tzinfo=KST))
            self.assertEqual(read_last_success(marker), date(2026, 11, 18))


if __name__ == "__main__":
    unittest.main()
