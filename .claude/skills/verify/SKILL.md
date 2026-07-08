---
name: verify
description: How to launch and drive this Streamlit app to verify UI changes end-to-end
---

# Verifying the SEO Analyzer locally

## Launch
```bash
source .venv/bin/activate
streamlit run app.py --server.port 8511 --server.headless true   # background it
```
- MUST be the Python 3.13 venv (3.14 breaks Streamlit/protobuf).
- First page load takes ~10s (SDK introspection builds the catalogue) — wait
  before screenshotting.
- Credentials auto-load from `.env.local`; the sidebar shows "Credentials loaded".

## Drive (claude-in-chrome)
- Home page has job shortcuts (e.g. "Check backlinks" → summary_live). For any
  other endpoint, type into the sidebar "Search all endpoints" box and press
  Enter — the top match is auto-selected.
- Streamlit widget gotchas: `form_input` often reports `Set text value to ""`
  and does nothing — click the field and use `type` instead. Text inputs commit
  on Enter; text areas commit on cmd+Enter or blur. Wait ~2s after committing
  for the rerun before screenshotting.
- Validation messages appear between the form and the Run button; advisory cost
  notes are blue st.info boxes, blocking problems are yellow st.warning boxes.
  Clicking Run with problems shows the red "no call was made" error.

## Cost warning
Run buttons make REAL paid DataForSEO calls on Jon's account. Backlinks calls
cost ~$0.024 + $0.000036/row — keep `limit` at 10 and use `dataforseo.com` /
`ahrefs.com` as targets. Validation-block paths cost nothing; prefer them.
