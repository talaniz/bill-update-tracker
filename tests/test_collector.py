import unittest
import json
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

from bill_update_tracker.observability import log_activity
from bill_update_tracker.windows import collection_window_start


class CollectorWindowTest(unittest.TestCase):
    @patch.dict("os.environ", {})
    def test_collection_window_uses_tracker_timezone(self):
        start = collection_window_start("America/Los_Angeles")
        self.assertEqual(start.tzinfo, timezone.utc)
        self.assertEqual(start.minute, 0)
        self.assertEqual(start.second, 0)

    @patch("bill_update_tracker.observability.activity_logger.info")
    def test_activity_event_is_structured_and_caller_controlled(self, log_info):
        log_activity("poll_failed", run_id=42, duration_ms=15, error_type="RuntimeError")

        payload = json.loads(log_info.call_args.args[0])
        self.assertEqual(
            payload,
            {
                "duration_ms": 15,
                "error_type": "RuntimeError",
                "event": "poll_failed",
                "run_id": 42,
            },
        )
        self.assertNotIn("error", payload)
        self.assertNotIn("api_key", payload)
        self.assertNotIn("message", payload)

    def test_activity_dashboard_includes_latest_poll_result(self):
        dashboard_path = Path(__file__).parents[1] / "grafana/dashboards/mothership-activity.json"
        dashboard = json.loads(dashboard_path.read_text())

        latest_result = next(panel for panel in dashboard["panels"] if panel["title"] == "Latest Poll Result")
        self.assertEqual(latest_result["type"], "logs")
        self.assertIn("poll_succeeded|poll_failed", latest_result["targets"][0]["expr"])


if __name__ == "__main__":
    unittest.main()
