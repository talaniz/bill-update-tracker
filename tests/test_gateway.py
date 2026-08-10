import unittest
from datetime import datetime, timezone

from bill_update_tracker.congress_gateway import CongressGateway


class GatewayTest(unittest.TestCase):
    def test_version_filter_rejects_older_versions(self):
        since = datetime(2026, 8, 10, tzinfo=timezone.utc)
        self.assertFalse(CongressGateway._version_is_since({"date": "2026-08-09"}, since))
        self.assertTrue(CongressGateway._version_is_since({"date": "2026-08-10"}, since))


if __name__ == "__main__":
    unittest.main()
