import unittest
from datetime import timezone

from bill_update_tracker.models import BILL_ACTION_UPDATE, BILL_SUMMARY_UPDATE, BILL_TEXT_UPDATE
from bill_update_tracker.normalize import (
    normalize_bill_action,
    normalize_summary,
    normalize_text_version,
    parse_congress_datetime,
)


class NormalizeTest(unittest.TestCase):
    def test_parse_congress_datetime_sets_utc(self):
        parsed = parse_congress_datetime("2026-08-10T12:34:56Z")
        self.assertEqual(parsed.tzinfo, timezone.utc)
        self.assertEqual(parsed.isoformat(), "2026-08-10T12:34:56+00:00")

    def test_normalize_bill_action(self):
        event = normalize_bill_action(
            {
                "congress": 119,
                "type": "HR",
                "number": "123",
                "latestAction": {
                    "actionDate": "2026-08-10",
                    "text": "Introduced in House",
                },
            }
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.source_type, BILL_ACTION_UPDATE)
        self.assertEqual(event.bill_type, "hr")
        self.assertIn("Introduced in House", event.event_key)

    def test_normalize_summary(self):
        event = normalize_summary(
            {
                "congress": 119,
                "type": "S",
                "number": "42",
                "versionCode": "00",
                "updateDate": "2026-08-10T01:02:03Z",
            }
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.source_type, BILL_SUMMARY_UPDATE)

    def test_normalize_text_version(self):
        event = normalize_text_version(
            {
                "congress": 119,
                "type": "HR",
                "number": "99",
                "versionCode": "ih",
                "date": "2026-08-10",
            }
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.source_type, BILL_TEXT_UPDATE)


if __name__ == "__main__":
    unittest.main()

