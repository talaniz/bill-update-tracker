from __future__ import annotations

from datetime import datetime
from typing import Any

from .normalize import parse_congress_datetime


class CongressGateway:
    """Fetches Congress.gov updates while keeping congress.py as the configured client library."""

    def __init__(self, api_key: str, api_root: str = "https://api.congress.gov/v3") -> None:
        if not api_key:
            raise ValueError("CONGRESS_API_KEY is required for live Congress.gov polling")
        self.api_key = api_key
        self.api_root = api_root.rstrip("/")
        self.client = self._build_congress_py_client(api_key)

    @staticmethod
    def _build_congress_py_client(api_key: str) -> Any:
        try:
            from congress_py import CongressClient
        except ImportError as exc:
            raise RuntimeError("Install congress-py before live polling") from exc
        return CongressClient(api_key)

    def fetch_updates_since(self, since: datetime) -> dict[str, list[dict[str, Any]]]:
        since_value = since.date().isoformat()
        return {
            "bill_actions": self._paged_get("bill", {"fromDateTime": since_value, "sort": "updateDate+desc"}),
            "summaries": self._paged_get(
                "summaries", {"fromDateTime": since_value, "sort": "updateDate+desc"}
            ),
            "text_versions": self._bill_text_versions_since(since),
        }

    def _paged_get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        offset = 0
        page_size = 250
        while True:
            payload = self._get(path, {**params, "limit": page_size, "offset": offset})
            page_items = payload.get("bills") or payload.get("summaries") or payload.get("textVersions") or []
            items.extend(page_items)
            pagination = payload.get("pagination") or {}
            count = int(pagination.get("count") or len(page_items))
            if count < page_size or not page_items:
                break
            offset += page_size
        return items

    def _bill_text_versions_since(self, since: datetime) -> list[dict[str, Any]]:
        bills = self._paged_get("bill", {"fromDateTime": since.date().isoformat(), "sort": "updateDate+desc"})
        text_versions: list[dict[str, Any]] = []
        for bill in bills:
            congress = bill.get("congress")
            bill_type = str(bill.get("type") or "").lower()
            number = bill.get("number")
            if not congress or not bill_type or not number:
                continue
            payload = self._get(f"bill/{congress}/{bill_type}/{number}/text", {})
            for version in payload.get("textVersions") or []:
                if not self._version_is_since(version, since):
                    continue
                text_versions.append(
                    {
                        **version,
                        "congress": congress,
                        "type": bill_type,
                        "number": number,
                    }
                )
        return text_versions

    @staticmethod
    def _version_is_since(version: dict[str, Any], since: datetime) -> bool:
        update_value = version.get("date") or version.get("updateDate") or version.get("lastUpdateDate")
        if not update_value:
            return False
        return parse_congress_datetime(update_value).date() >= since.date()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        return self.client._get(
            f"{self.api_root}/{path.lstrip('/')}",
            params={**params, "format": "json"},
        )
