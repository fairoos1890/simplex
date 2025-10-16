"""Client for retrieving TRC20 transfers from TronScan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Dict, List
from urllib.parse import urlencode
from urllib.request import urlopen

from .config import MonitorSettings, StaffAccount


@dataclass(slots=True)
class Transfer:
    """Represents a single TRC20 transfer."""

    tx_hash: str
    timestamp: datetime
    sender: str
    recipient: str
    amount: Decimal
    token_symbol: str


class TronScanClient:
    """Thin wrapper around the public TronScan TRC20 transfer API."""

    def __init__(self, settings: MonitorSettings) -> None:
        self._settings = settings

    def _make_request(self, params: Dict[str, object]) -> Dict[str, object]:
        query = urlencode(params)
        url = f"{self._settings.api_base_url}/token_trc20/transfers?{query}"
        with urlopen(url, timeout=30) as response:  # type: ignore[arg-type]
            payload = response.read()
        return json.loads(payload)

    def fetch_transfers(self, staff: StaffAccount) -> List[Transfer]:
        """Fetch transfers involving ``staff`` for the configured TRC20 token."""

        transfers: List[Transfer] = []
        cutoff = None
        if self._settings.total_history_days:
            cutoff = datetime.utcnow() - timedelta(days=self._settings.total_history_days)

        for page in range(self._settings.pages):
            params = {
                "limit": self._settings.page_size,
                "start": page * self._settings.page_size,
                "contract_address": self._settings.token_contract,
                "relatedAddress": staff.address,
                "sort": "-timestamp",
            }
            data = self._make_request(params)
            for item in data.get("data", []):
                tx_hash = item.get("transaction_id") or item.get("hash")
                timestamp = datetime.fromtimestamp(item["timestamp"] / 1000)
                if cutoff and timestamp < cutoff:
                    continue
                amount = Decimal(item.get("quant", "0")) / Decimal(self._settings.scale)
                transfers.append(
                    Transfer(
                        tx_hash=tx_hash,
                        timestamp=timestamp,
                        sender=item.get("from_address"),
                        recipient=item.get("to_address"),
                        amount=amount,
                        token_symbol=self._settings.token_symbol,
                    )
                )
            if len(data.get("data", [])) < self._settings.page_size:
                break
        return transfers


__all__ = ["Transfer", "TronScanClient"]
