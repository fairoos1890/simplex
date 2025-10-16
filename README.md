# TRC20 Staff Monitor

This repository provides a small command line helper that pulls recent TRC20 token
transfers for your staff wallets and highlights potential red flags such as high
value transfers, uncommon counterparties, links between staff wallets, and burst
activity.

## Getting started

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create a configuration file**

   Copy `config.sample.yaml` to `config.yaml` and edit it to include:

   - the TRC20 token contract address, symbol, and decimals,
   - a list of staff wallets (optionally labelled with names), and
   - thresholds for what you consider unusual activity (for example the lookback
     window, high value amount, and burst detection settings).

3. **Run the monitor**

   ```bash
   python -m simplex config.yaml
   ```

   Use `--dry-run` to simply validate the configuration without making API calls.

## How it works

* `simplex.client.TronScanClient` queries the public TronScan API for TRC20
  transfers involving each staff wallet.
* `simplex.analysis.analyse_transfers` summarises inbound/outbound totals,
  finds high-value transfers, lists counterparties that have appeared less than
  the configured threshold, highlights other staff wallets that interact with
  the address, and flags bursts of activity within a moving time window.
* The CLI prints a human-readable summary so you can easily spot anomalies.

## Testing

Install `pytest` and run the unit tests:

```bash
pip install pytest
pytest
```
