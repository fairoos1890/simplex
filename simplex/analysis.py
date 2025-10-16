"""Analysis utilities for TRC20 transfers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence

from .client import Transfer
from .config import MonitorSettings, StaffAccount


@dataclass(slots=True)
class AddressSummary:
    staff: StaffAccount
    token_symbol: str
    total_in: Decimal
    total_out: Decimal
    net: Decimal
    transfer_count: int
    high_value_transfers: List[Transfer]
    uncommon_counterparties: List[str]
    linked_staff: List[str]
    burst_windows: List[str]


def analyse_transfers(
    transfers: Sequence[Transfer],
    *,
    staff: StaffAccount,
    all_staff_addresses: Iterable[str],
    settings: MonitorSettings,
) -> AddressSummary:
    """Analyse transfers for a single staff member and return an :class:`AddressSummary`."""

    total_in = Decimal("0")
    total_out = Decimal("0")
    high_value_transfers: List[Transfer] = []
    counterparty_counter: Counter[str] = Counter()
    linked_staff: List[str] = []

    ordered = sorted(transfers, key=lambda t: t.timestamp)
    timestamps = [t.timestamp for t in ordered]

    for transfer in transfers:
        if transfer.recipient.lower() == staff.address.lower():
            total_in += transfer.amount
        if transfer.sender.lower() == staff.address.lower():
            total_out += transfer.amount
        if transfer.amount >= Decimal(str(settings.high_value_threshold)):
            high_value_transfers.append(transfer)
        other_party = transfer.recipient if transfer.sender.lower() == staff.address.lower() else transfer.sender
        if other_party:
            counterparty_counter[other_party] += 1

    staff_addresses = {addr.lower() for addr in all_staff_addresses if addr.lower() != staff.address.lower()}
    linked_staff = [addr for addr in counterparty_counter if addr.lower() in staff_addresses]

    uncommon_counterparties = [
        addr
        for addr, count in counterparty_counter.items()
        if count <= settings.uncommon_counterparty_threshold and addr.lower() not in staff_addresses
    ]

    burst_windows = _detect_bursts(timestamps, settings)

    return AddressSummary(
        staff=staff,
        token_symbol=settings.token_symbol,
        total_in=total_in,
        total_out=total_out,
        net=total_in - total_out,
        transfer_count=len(transfers),
        high_value_transfers=sorted(high_value_transfers, key=lambda t: t.amount, reverse=True),
        uncommon_counterparties=sorted(uncommon_counterparties),
        linked_staff=sorted(linked_staff),
        burst_windows=burst_windows,
    )


def _detect_bursts(timestamps: Sequence[datetime], settings: MonitorSettings) -> List[str]:
    if not timestamps:
        return []
    window = timedelta(hours=settings.burst_window_hours)
    bursts: List[str] = []
    for i, start in enumerate(timestamps):
        end_window = start + window
        count = 1
        for j in range(i + 1, len(timestamps)):
            if timestamps[j] <= end_window:
                count += 1
            else:
                break
        if count >= settings.burst_transfer_threshold:
            bursts.append(f"{start.isoformat()} - {(start + window).isoformat()} ({count} transfers)")
    return bursts


__all__ = ["AddressSummary", "analyse_transfers"]
