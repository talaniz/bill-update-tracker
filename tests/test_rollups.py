import unittest
from datetime import datetime, timezone

from bill_update_tracker.models import BILL_ACTION_UPDATE, BILL_SUMMARY_UPDATE, UpdateEvent
from bill_update_tracker.rollups import rollup_events_in_memory


class RollupTest(unittest.TestCase):
    def test_rolls_up_by_day_and_type(self):
        events = [
            UpdateEvent("a", BILL_ACTION_UPDATE, datetime(2026, 8, 10, tzinfo=timezone.utc)),
            UpdateEvent("b", BILL_ACTION_UPDATE, datetime(2026, 8, 10, 1, tzinfo=timezone.utc)),
            UpdateEvent("c", BILL_SUMMARY_UPDATE, datetime(2026, 8, 10, 2, tzinfo=timezone.utc)),
        ]
        rollup = rollup_events_in_memory(events)
        self.assertEqual(rollup[("2026-08-10", BILL_ACTION_UPDATE)], 2)
        self.assertEqual(rollup[("2026-08-10", BILL_SUMMARY_UPDATE)], 1)


if __name__ == "__main__":
    unittest.main()
