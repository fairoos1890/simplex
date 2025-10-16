"""Configuration helpers for the TRC20 monitoring CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(slots=True)
class StaffAccount:
    """Represents a staff wallet we want to monitor."""

    name: str
    address: str


@dataclass(slots=True)
class MonitorSettings:
    """Holds the configuration necessary to fetch and analyse transfers."""

    token_contract: str
    token_symbol: str
    token_decimals: int
    staff: List[StaffAccount]
    total_history_days: int = 30
    high_value_threshold: float = 1000.0
    burst_transfer_threshold: int = 5
    burst_window_hours: int = 24
    uncommon_counterparty_threshold: int = 1
    api_base_url: str = "https://apilist.tronscanapi.com/api"
    page_size: int = 50
    pages: int = 2

    @property
    def scale(self) -> int:
        return 10 ** self.token_decimals


def _validate_staff(entries: Iterable[dict]) -> List[StaffAccount]:
    staff = []
    for entry in entries:
        if "address" not in entry:
            raise ValueError("Each staff entry must include an 'address' field.")
        name = entry.get("name") or entry["address"]
        staff.append(StaffAccount(name=name, address=entry["address"].strip()))
    if not staff:
        raise ValueError("Configuration must define at least one staff address.")
    return staff


def load_settings(path: str | Path) -> MonitorSettings:
    """Load a :class:`MonitorSettings` instance from a YAML file."""

    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency guard
        raise ModuleNotFoundError(
            "PyYAML is required to load configuration files. Install it with 'pip install PyYAML'."
        ) from exc

    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Configuration file must contain a mapping at the top level.")

    token = data.get("token") or {}
    staff_entries = data.get("staff") or []

    settings = MonitorSettings(
        token_contract=token.get("contract"),
        token_symbol=token.get("symbol", "UNKNOWN"),
        token_decimals=int(token.get("decimals", 6)),
        staff=_validate_staff(staff_entries),
        total_history_days=int(data.get("total_history_days", 30)),
        high_value_threshold=float(data.get("high_value_threshold", 1000)),
        burst_transfer_threshold=int(data.get("burst_transfer_threshold", 5)),
        burst_window_hours=int(data.get("burst_window_hours", 24)),
        uncommon_counterparty_threshold=int(data.get("uncommon_counterparty_threshold", 1)),
        api_base_url=data.get("api_base_url", "https://apilist.tronscanapi.com/api"),
        page_size=int(data.get("page_size", 50)),
        pages=int(data.get("pages", 2)),
    )

    if not settings.token_contract:
        raise ValueError("The configuration must provide token.contract")

    return settings


__all__ = ["StaffAccount", "MonitorSettings", "load_settings"]
