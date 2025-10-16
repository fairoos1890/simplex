"""Command line interface for the TRC20 monitoring helper."""

from __future__ import annotations

import argparse
from typing import List

from .analysis import AddressSummary, analyse_transfers, find_shared_counterparties
from .client import TronScanClient
from .config import MonitorSettings, StaffAccount, load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyse TRC20 transfers for staff wallets")
    parser.add_argument("config", help="Path to the YAML configuration file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip API calls and only validate configuration",
    )
    return parser


def render_summary(summary: AddressSummary) -> str:
    lines = [f"Staff: {summary.staff.name} ({summary.staff.address})"]
    symbol = summary.token_symbol
    lines.append(f"  Total in : {summary.total_in} {symbol}")
    lines.append(f"  Total out: {summary.total_out} {symbol}")
    lines.append(f"  Net      : {summary.net} {symbol}")
    lines.append(f"  Transfers: {summary.transfer_count}")

    if summary.high_value_transfers:
        lines.append("  High value transfers:")
        for transfer in summary.high_value_transfers[:10]:
            direction = "IN" if transfer.recipient.lower() == summary.staff.address.lower() else "OUT"
            lines.append(
                f"    - {direction} {transfer.amount} {symbol} on {transfer.timestamp.isoformat()} (tx: {transfer.tx_hash})"
            )
    if summary.uncommon_counterparties:
        lines.append("  Uncommon counterparties: " + ", ".join(summary.uncommon_counterparties[:10]))
    if summary.linked_staff:
        lines.append("  Linked staff wallets: " + ", ".join(summary.linked_staff))
    if summary.burst_windows:
        lines.append("  Burst activity windows:")
        lines.extend(f"    - {window}" for window in summary.burst_windows)
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = load_settings(args.config)
    except Exception as exc:  # pragma: no cover - CLI guard
        parser.error(str(exc))
        return 2

    if args.dry_run:
        print("Configuration loaded successfully. Dry run complete.")
        return 0

    client = TronScanClient(settings)
    staff_addresses = [member.address for member in settings.staff]

    summaries: List[AddressSummary] = []
    for member in settings.staff:
        transfers = client.fetch_transfers(member)
        summary = analyse_transfers(transfers, staff=member, all_staff_addresses=staff_addresses, settings=settings)
        summaries.append(summary)
        print(render_summary(summary))
        print("-" * 80)

    shared = find_shared_counterparties(summaries)
    if shared:
        print("Shared counterparties across staff wallets:")
        for counterparty, names in sorted(shared.items()):
            print(f"  - {counterparty}: {', '.join(names)}")

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
