import unittest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from bill_update_tracker.congress_gateway import CongressGateway, CongressGatewayError


class GatewayTest(unittest.TestCase):
    def test_version_filter_rejects_older_versions(self):
        since = datetime(2026, 8, 10, tzinfo=timezone.utc)
        self.assertFalse(CongressGateway._version_is_since({"date": "2026-08-09"}, since))
        self.assertTrue(CongressGateway._version_is_since({"date": "2026-08-10"}, since))

    def test_fetch_uses_full_datetime_and_supported_sort(self):
        gateway = object.__new__(CongressGateway)
        gateway._path = Mock(side_effect=lambda collection: collection)
        gateway._paged_get = Mock(return_value=[])
        gateway._bill_text_versions_since = Mock(return_value=[])

        since = datetime(2026, 8, 10, 7, tzinfo=timezone.utc)
        gateway.fetch_updates_since(since)

        self.assertEqual(
            gateway._paged_get.call_args_list[0].args,
            ("bill", {"fromDateTime": "2026-08-10T07:00:00Z", "sort": "updateDate desc"}),
        )
        self.assertEqual(
            gateway._paged_get.call_args_list[1].args,
            ("summaries", {"fromDateTime": "2026-08-10T07:00:00Z", "sort": "updateDate desc"}),
        )

    def test_path_defaults_to_current_congress(self):
        gateway = object.__new__(CongressGateway)
        gateway.target_congress = None
        gateway.track_current_congress_only = True
        gateway._get = Mock(return_value={"congress": {"number": 119}})

        self.assertEqual(gateway._path("bill"), "bill/119")

    def test_path_can_use_all_congresses(self):
        gateway = object.__new__(CongressGateway)
        gateway.target_congress = None
        gateway.track_current_congress_only = False

        self.assertEqual(gateway._path("bill"), "bill")

    def test_request_timeout_error_never_contains_api_key_or_url(self):
        class RequestException(Exception):
            pass

        class HTTPError(RequestException):
            response = None

        class Timeout(RequestException):
            pass

        gateway = object.__new__(CongressGateway)
        gateway.api_key = "not-a-real-key"
        gateway.api_root = "https://api.congress.gov/v3"
        gateway.client = Mock()
        gateway.client.session.get.side_effect = Timeout(
            "https://api.congress.gov/v3/bill?token=not-a-real-key"
        )

        fake_requests = SimpleNamespace(RequestException=RequestException, HTTPError=HTTPError)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            with self.assertRaises(CongressGatewayError) as raised:
                gateway._get("bill", {})

        self.assertEqual(str(raised.exception), "error_type=Timeout")
        self.assertNotIn("not-a-real-key", str(raised.exception))
        self.assertNotIn("https://", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
