# SEO Analyzer Tool

## START HERE, EVERY SESSION
**Read `docs/PROJECT-STATUS.md` first** — it is the living working document for this
project (current status, how to run/test, architecture, decisions, gotchas, what's
left, and a session log). Keep it updated as you make changes.

## Essentials (full detail in docs/PROJECT-STATUS.md)
- Auto-generated Streamlit gateway over the full DataForSEO API. Entry: `app.py`.
- **Use Python 3.13** (`python3.13 -m venv .venv`). Python 3.14 breaks Streamlit/protobuf.
- Run: `source .venv/bin/activate && streamlit run app.py --server.port 8501`
- Test: `python -m pytest -q` (77 passing).
- Phases 0–5 done locally on `main`; **NOT deployed**. Deploy (push + Railway Postgres)
  needs Jon's explicit go-ahead — do not push/deploy without it.
- Old monolith preserved at `archive/app_v1.py`.
