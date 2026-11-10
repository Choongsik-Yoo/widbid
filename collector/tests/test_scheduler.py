from datetime import datetime, timedelta, timezone
import unittest

from scheduler import next_run_at


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


if __name__ == "__main__":
    unittest.main()
