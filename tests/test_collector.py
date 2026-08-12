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

    def test_tracker_dashboard_includes_hourly_discovery_cadence_panels(self):
        dashboard_path = Path(__file__).parents[1] / "grafana/dashboards/bill-update-tracker.json"
        dashboard = json.loads(dashboard_path.read_text())
        panels = {panel["title"]: panel for panel in dashboard["panels"]}

        hourly_updates = panels["New Updates Discovered Per Hour"]
        self.assertIn("status = 'success'", hourly_updates["targets"][0]["rawSql"])
        self.assertIn("SUM(inserted_events)", hourly_updates["targets"][0]["rawSql"])
        self.assertIn("$__timeFilter(finished_at)", hourly_updates["targets"][0]["rawSql"])

        hourly_result = panels["Poll Result Per Hour"]
        self.assertIn("CASE WHEN inserted_events > 0 THEN 1 ELSE 0 END", hourly_result["targets"][0]["rawSql"])
        self.assertIn("status = 'success'", hourly_result["targets"][0]["rawSql"])

        active_day = panels["Discovery Polls Per Active Day"]
        self.assertIn("inserted_events > 0", active_day["targets"][0]["rawSql"])
        self.assertIn("EXTRACT(ISODOW FROM finished_at) BETWEEN 1 AND 5", active_day["targets"][0]["rawSql"])
        self.assertIn("30 active weekdays", active_day["description"])


if __name__ == "__main__":
    unittest.main()
