# SEO Analyzer Tool

A bring-your-own-key Streamlit gateway to the **full DataForSEO API**. Forms for
every endpoint are auto-generated from the official `dataforseo-client` SDK, so all
13 API families (~396 logical operations) are available without hand-coding each one.

## Features

- **Every DataForSEO endpoint** — SERP, Keywords Data, DataForSEO Labs, AI
  Optimization (ChatGPT/Claude/Gemini/Perplexity + AI Overview), Backlinks, On-Page,
  Business Data, Merchant, App Data, Domain Analytics, Content Analysis/Generation.
- **Auto-generated forms** with friendly labels and per-field markers
  (`required` / `required unless X set` / `optional` / `default: …`).
- **Quick-pick dropdowns** for common locations and languages, plus model
  dropdowns for LLM endpoints — with free-text fallback.
- **Smart results** — summary metrics, a clean table, LLM/AI answers rendered as
  text, and raw JSON. CSV + JSON export on every result.
- **Global endpoint search**, **task-based endpoint polling**, **run history**,
  **saved presets**, **account balance widget**, **cost estimates**,
  **shareable links**, and **bulk-run from CSV**.

## Running locally

```bash
python3.13 -m venv .venv && source .venv/bin/activate   # Python 3.13 (see below)
pip install -r requirements.txt
streamlit run app.py
```

Credentials are read from `.env.local` (`user_name` / `password`) or entered in the
sidebar. Run history and presets persist to a local SQLite file under `data/`.

## Deployment (Railway)

- Set `DATABASE_URL` to a Railway Postgres instance for durable history/presets
  (falls back to local SQLite when unset).
- `Procfile` / `railway.json` run `streamlit run app.py`.
- **Python 3.13 is required** (`.python-version`). Python 3.14 breaks Streamlit's
  protobuf dependency.

## Architecture

```
app.py                     # thin entry point -> seo_analyser.ui.app:main
seo_analyser/
├── registry/    # SDK introspection, endpoint catalogue, overrides
├── forms/       # request-model -> widget specs and rendering
├── runner/      # live + task-based execution, error normalisation, lookups
├── results/     # response detection, rendering, export
├── billing/     # balance + cost estimates
├── persistence/ # SQLAlchemy store (Postgres / SQLite)
└── ui/          # sidebar, endpoint page, sharing, app shell
```

The previous single-file app is preserved at `archive/app_v1.py`.
