import unittest
from datetime import timezone
from unittest.mock import patch

from bill_update_tracker.windows import collection_window_start


class CollectorWindowTest(unittest.TestCase):
    @patch.dict("os.environ", {})
    def test_collection_window_uses_tracker_timezone(self):
        start = collection_window_start("America/Los_Angeles")
        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)


if __name__ == "__main__":
    unittest.main()
