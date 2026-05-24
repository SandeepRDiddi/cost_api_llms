# LLM Cost Explorer

Python CLI that fetches official LLM pricing pages, normalizes token pricing, and updates one master Excel workbook for ongoing analysis.

## What it does

- pulls pricing from official vendor pages
- normalizes comparable token pricing into one schema
- updates one persistent `XLSX` master workbook
- supports daily and manual refresh via GitHub Actions
- keeps `source_status`, history, and run metadata inside the workbook

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
PYTHONPATH=src python3 -m cost_explorer --output-dir data
PYTHONPATH=src python3 -m cost_explorer --allow-partial
```

## Outputs

- `data/llm_costs.xlsx`

## Excel sheets

- `prices_current`
- `source_status`
- `vendor_summary`
- `price_history`
- `run_metadata`

Each run refreshes the current-summary sheets and appends any new snapshot rows into `price_history` in the same workbook, so `data/llm_costs.xlsx` is the master file.

## Testing

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## GitHub Actions

The workflow runs daily and can also be triggered manually:

- schedule: `0 6 * * *`
- manual: `workflow_dispatch`

It installs dependencies, updates `data/llm_costs.xlsx`, commits that workbook back to the repository when it changes, and uploads the workbook as an artifact.
