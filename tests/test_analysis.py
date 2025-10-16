from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from simplex.analysis import analyse_transfers
from simplex.client import Transfer
from simplex.config import MonitorSettings, StaffAccount


def make_transfer(ts_offset_hours: int, *, sender: str, recipient: str, amount: str) -> Transfer:
    ts = datetime(2024, 1, 1) + timedelta(hours=ts_offset_hours)
    return Transfer(
        tx_hash=f"tx-{ts_offset_hours}",
        timestamp=ts,
        sender=sender,
        recipient=recipient,
        amount=Decimal(amount),
        token_symbol="USDT",
    )


def test_analyse_transfers_flags_high_value_and_uncommon_counterparties():
    settings = MonitorSettings(
        token_contract="contract",
        token_symbol="USDT",
        token_decimals=6,
        staff=[StaffAccount(name="Alice", address="TAlice"), StaffAccount(name="Bob", address="TBob")],
        high_value_threshold=500,
        uncommon_counterparty_threshold=2,
        burst_transfer_threshold=3,
        burst_window_hours=24,
    )

    transfers = [
        make_transfer(0, sender="TAlice", recipient="TCounter1", amount="100"),
        make_transfer(1, sender="TCounter1", recipient="TAlice", amount="600"),  # high value
        make_transfer(2, sender="TAlice", recipient="TBob", amount="50"),  # linked staff
        make_transfer(3, sender="TAlice", recipient="TCounter2", amount="10"),
    ]

    summary = analyse_transfers(
        transfers,
        staff=settings.staff[0],
        all_staff_addresses=[member.address for member in settings.staff],
        settings=settings,
    )

    assert summary.total_in == Decimal("600")
    assert summary.total_out == Decimal("160")
    assert summary.token_symbol == "USDT"
    assert summary.high_value_transfers[0].amount == Decimal("600")
    assert "TCounter1" in summary.uncommon_counterparties
    assert "TBob" in summary.linked_staff


def test_burst_detection_returns_window_when_threshold_met():
    settings = MonitorSettings(
        token_contract="contract",
        token_symbol="USDT",
        token_decimals=6,
        staff=[StaffAccount(name="Alice", address="TAlice")],
        high_value_threshold=500,
        uncommon_counterparty_threshold=1,
        burst_transfer_threshold=2,
        burst_window_hours=1,
    )

    transfers = [
        make_transfer(0, sender="TAlice", recipient="TCounter1", amount="10"),
        make_transfer(0, sender="TAlice", recipient="TCounter2", amount="10"),
    ]

    summary = analyse_transfers(
        transfers,
        staff=settings.staff[0],
        all_staff_addresses=[member.address for member in settings.staff],
        settings=settings,
    )

    assert len(summary.burst_windows) == 1
    assert "(2 transfers)" in summary.burst_windows[0]
