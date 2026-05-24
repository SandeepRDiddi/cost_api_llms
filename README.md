# LLM Cost Explorer

Python CLI that fetches official LLM pricing pages, normalizes token pricing into flat datasets, and exports Excel-friendly outputs for daily analysis.

## What it does

- pulls pricing from official vendor pages
- normalizes comparable token pricing into one schema
- exports `CSV`, `JSON`, and `XLSX`
- stores dated snapshots for historical analysis
- supports daily and manual refresh via GitHub Actions
- keeps a `source_status` report so coverage and failures are visible

## Current coverage

### Active official-source adapters

- OpenAI — `https://developers.openai.com/api/docs/pricing?latest-pricing=flex`
- Anthropic — `https://www.anthropic.com/pricing#api`
- Google Gemini API — `https://ai.google.dev/gemini-api/docs/pricing?hl=en`
- xAI — `https://docs.x.ai/docs/pricing`

### Explicitly tracked but not yet parsed

- Mistral — current public pricing page is consumer/subscription oriented and does not expose a stable API token table
- Cohere — current public pricing page exposes enterprise/model-vault pricing, not a stable public API token table

Those two vendors are included in the source-status output as unsupported rather than silently omitted.

## Accuracy model

This project does **not** claim guaranteed universal accuracy. Instead, it is designed for traceable accuracy:

- every row includes the official `source_url`
- every run includes `fetched_at`
- supported parsers fail loudly if an official page changes in a way that breaks extraction
- unsupported vendors are surfaced explicitly in `source_status`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
PYTHONPATH=src python3 -m cost_explorer
```

Optional flags:

```bash
PYTHONPATH=src python3 -m cost_explorer --output-dir data --history-dir data/history
PYTHONPATH=src python3 -m cost_explorer --allow-partial
```

## Outputs

- `data/prices_current.csv`
- `data/prices_current.json`
- `data/source_status.csv`
- `data/prices_history.csv`
- `data/llm_costs.xlsx`
- `data/history/prices_<timestamp>.csv`

## Excel sheets

- `prices_current`
- `source_status`
- `vendor_summary`
- `price_history`

## GitHub Actions

The workflow runs daily and can also be triggered manually:

- schedule: `0 6 * * *`
- manual: `workflow_dispatch`

It installs dependencies, runs the exporter, and uploads the generated files as artifacts.
