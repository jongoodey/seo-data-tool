# SEO Analyzer Tool — Project Overview

**Status:** Brainstorming / pre-spec
**Date:** 2026-05-29
**Author:** Jon Goodey (Indexify)
**Working name:** SEO Analyzer Tool (rename from "AI Keyword Analyser")

---

## 1. TL;DR

The project today is a 3,550-line Streamlit app that surfaces ~30 DataForSEO endpoints behind hand-rolled forms. The brief is to turn it into a **bring-your-own-key universal gateway to DataForSEO**, exposing as much of the API surface as possible. DataForSEO ships **565 unique endpoints across 13 API families** (~350-400 logical operations once task-based triplets are collapsed), so the only realistic path is **auto-generating forms from their official PythonClient SDK** rather than hand-coding each one.

> **Companion documents:**
> - `current-app-audit.md` — detailed audit of what `app.py` does today
> - `sdk-technical-analysis.md` — proof that SDK introspection drives auto-generation
> - `endpoint-inventory.md` — concrete inventory of all 565 endpoints, grouped by family

Direction agreed in brainstorming:

- **Auto-generated UI** driven by SDK introspection (one generic endpoint runner, not 1,130 hand-coded pages)
- **Source of truth:** the official [`dataforseo-client`](https://github.com/dataforseo/PythonClient) SDK (which is itself generated from their OpenAPI YAML)
- **Clean rebuild** of `app.py` into modular structure, staying on Streamlit + Railway
- **Smart auto-detection** of response shape for results (table / chart / tree / JSON)
- **v1 features:** run history + saved presets, plus endpoint search and CSV/JSON export as baselines

---

## 2. What we have today

### 2.1 Repo contents

```
ai-overviews/
├── app.py                 # 3,550 lines, single file, monolithic
├── requirements.txt       # streamlit, pandas, plotly, requests
├── README.md              # describes only 3 features (out of date)
├── Procfile               # streamlit run app.py --server.port $PORT ...
├── railway.json           # Railway deploy config
├── .env.local             # DataForSEO creds (gitignored)
├── .streamlit/config.toml # theme, headless, CORS
└── .claude/settings.local.json
```

### 2.2 Current app architecture

One file, four conceptual layers smashed together:

| Lines      | What's there                                                                 |
|------------|------------------------------------------------------------------------------|
| 17–622     | `DataForSEOClient` class — ~30 hand-coded methods, one per endpoint           |
| 623–743    | Helpers (response parsing, plotly chart builders)                            |
| 744–end    | One huge `main()` with nested `if function_category == ...` for each tool    |

### 2.3 Endpoints already wired

| Category         | Endpoint method                                            |
|------------------|------------------------------------------------------------|
| **AI Optimisation**  | `get_keyword_search_volume`, `get_llm_response`, `get_google_ai_overview` |
| **Backlinks**        | `get_backlinks`, `get_broken_backlinks`, `get_backlink_anchors`, `get_referring_domains`, `get_backlink_summary`, `get_bulk_backlinks`, `get_bulk_referring_domains`, `get_bulk_ranks`, `get_bulk_spam_score`, `get_bulk_new_lost_backlinks`, `get_bulk_new_lost_referring_domains` |
| **SERP & Rankings**  | `get_serp_organic`, `get_bulk_serp`, `get_domain_rank_overview`, `get_historical_rank_overview`, `get_ranked_keywords`, `get_instant_pages` |
| **Keywords**         | `get_keyword_suggestions`, `get_keyword_ideas`, `get_keywords_for_site`, `get_keywords_for_categories`, `get_search_intent`, `get_bulk_keyword_difficulty`, `get_google_search_volume`, `get_bing_search_volume` |

That's ~30 endpoints out of 1,130 (~2.7%).

### 2.4 Existing UX patterns worth preserving

- Sidebar config (creds + location/language) — keep
- Tabbed result views (Overview / Charts / Data Table / Export) — generalise
- Plotly comparison + trend charts — fold into auto-detect renderer
- CSV / JSON download buttons — keep as universal export

### 2.5 Existing pain points

- One file, untestable, friction high to add an endpoint
- Hand-coded location/language lists (~30 countries, 17 languages) — DataForSEO actually supports hundreds
- No run history, no saved queries, no shareable links
- `_get_country_code` is a manual lookup table that will rot
- Credentials prompt every refresh; no session persistence beyond Streamlit's default
- README claims 3 features but ~30 exist — docs already drift

---

## 3. The full DataForSEO surface

The official SDK exposes 13 API families. Endpoint counts measured directly from the SDK's URI tables (see `endpoint-inventory.md` for the breakdown by sub-endpoint):

| API family            | Endpoints | What it covers                                                                                            |
|-----------------------|-----------|------------------------------------------------------------------------------------------------------------|
| **SERP**              | 181       | Google (105), YouTube (23), Yahoo (12), Bing (12), Seznam (9), Baidu (9), Naver (6)                       |
| **Keywords Data**     | 70        | Google Ads, Bing Ads, Google Trends, DataForSEO Trends, Clickstream                                       |
| **Business Data**     | 55        | Google My Business, Trustpilot, Tripadvisor, social media signals, business listings                      |
| **DataForSEO Labs**   | 47        | Keyword ideas, suggestions, ranked keywords, search intent, traffic estimation, competitor research       |
| **AI Optimization**   | 44        | LLM responses (ChatGPT, Claude, Gemini, Perplexity), LLM mentions tracking, AI search volume              |
| **App Data**          | 42        | Apple App Store, Google Play app metadata, reviews, rankings                                              |
| **Merchant**          | 32        | Amazon products, ASIN, sellers, Google Shopping                                                           |
| **On-Page**           | 31        | Site audits, page parsing, lighthouse, redirect chains, raw HTML, duplicates                              |
| **Backlinks**         | 24        | Anchors, summary, referring domains, bulk metrics, page/domain intersection, history, timeseries          |
| **Domain Analytics**  | 14        | Technologies stack, Whois, domain metadata                                                                |
| **Content Analysis**  | 11        | Mentions search, phrase trends, sentiment, summary, ratings                                               |
| **Content Generation**| 10        | Generate, paraphrase, grammar/check, meta tag generation                                                  |
| **Appendix**          | 4         | User data (drives balance widget), status, webhook resend, errors                                         |
| **Total**             | **565**   |                                                                                                            |

> The previous figure of ~1,130 in earlier drafts double-counted some entries. The deduplicated count from the SDK's URI tables is **565**. Many task-based endpoints appear as triplets (`task_post` + `tasks_ready` + `task_get_*`) — the UI collapses each triplet into a single logical operation, giving a user-facing count closer to **~350–400 operations**.

Two request shapes across all of them:

1. **Live** — single HTTP call, response now (e.g. `/v3/serp/google/organic/live/advanced`)
2. **Task-based** — `task_post` → poll `tasks_ready` → fetch via `task_get/{id}` (e.g. for SERP types where Google rate-limits or for batch crawls). Must be modelled in the UI as async.

Auth: HTTP Basic with the DataForSEO login + password — same as today.

---

## 4. Decisions locked in brainstorming

| # | Decision                  | Choice                                                   |
|---|---------------------------|----------------------------------------------------------|
| 1 | Endpoint strategy         | Auto-generated forms (universal endpoint dispatcher)      |
| 2 | Spec source               | Official `dataforseo-client` PythonClient SDK             |
| 3 | Migration path            | Clean rebuild, keep Streamlit + Railway                   |
| 4 | Results presentation      | Smart auto-detection (table / chart / tree / raw JSON)    |
| 5 | v1 personal feature       | Run history + saved presets                               |
| 6 | Product name              | "SEO Analyzer Tool"                                       |

Baseline assumptions (treating as non-optional at this scale):

- Endpoint search / fuzzy filter in the sidebar
- Universal CSV / JSON export from any result view
- BYOK auth via sidebar (already works today)

---

## 5. Proposed architecture

### 5.1 Module layout

```
ai-overviews/
├── app.py                       # thin entrypoint, just main()
├── seo_analyser/
│   ├── __init__.py
│   ├── auth.py                  # credentials + session state
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── introspect.py        # walk dataforseo_client.api.*, extract methods + request models
│   │   ├── catalogue.py         # cached endpoint catalogue (family → endpoints → params)
│   │   └── overrides.yml        # per-endpoint UX hints (labels, hide/show, defaults)
│   ├── forms/
│   │   ├── builder.py           # turn an endpoint signature into Streamlit widgets
│   │   ├── widgets.py           # field-type → widget mapping (string → text, enum → select, list → text_area + parser)
│   │   └── validators.py        # client-side checks before submit
│   ├── runner/
│   │   ├── live.py              # execute live endpoints
│   │   ├── tasks.py             # post → poll → get flow for task-based endpoints
│   │   └── errors.py            # uniform error normalisation + retry
│   ├── results/
│   │   ├── detect.py            # shape detection: list[dict] → table, time series → chart, etc.
│   │   ├── renderers.py         # plotly + st.dataframe + nested viewers
│   │   └── export.py            # CSV / JSON / parquet
│   ├── history/
│   │   ├── store.py             # in-session + on-disk persistence
│   │   └── presets.py           # save / load named presets
│   └── ui/
│       ├── sidebar.py           # creds, search, family → endpoint picker
│       ├── endpoint_page.py     # form + run + results
│       └── home.py              # landing, recent runs, presets
├── tests/
│   ├── test_introspect.py
│   ├── test_form_builder.py
│   └── test_result_detect.py
├── requirements.txt             # + dataforseo-client, + pydantic
├── Procfile
└── docs/
    └── seo-analyser-overview.md (this file)
```

### 5.2 Core flow

1. **Introspection** runs once at startup (cached): walk every class in `dataforseo_client.api.*`, list its public methods, pull the request-model class from the type hint, extract field names + types + docstrings.
2. **Catalogue** stores `{family: [{endpoint, http_path, request_model, fields, is_task_based}, ...]}`.
3. **Sidebar** renders family + endpoint pickers driven by the catalogue, with a fuzzy search box across all endpoint names + paths.
4. **Form builder** takes the selected endpoint's request model, builds Streamlit widgets per field (`str` → `text_input`, `List[str]` → `text_area` parsed by newline/comma, `enum` → `selectbox`, `bool` → `checkbox`, `int` → `number_input` with min/max from the model).
5. **Runner** instantiates the SDK API class with current credentials, calls the method with the parsed payload. For task-based endpoints it shows a progress indicator and polls.
6. **Results detector** inspects the response shape and picks a renderer; raw JSON is always available as a fallback tab.
7. **History** writes each run (endpoint, params hash, timestamp, response size) to session state and an optional on-disk file; "Re-run" loads the params back into the form.

### 5.3 Per-endpoint overrides

A YAML file (`registry/overrides.yml`) lets us upgrade specific endpoints without forking the auto-generated flow:

```yaml
serp.google_organic_live_advanced:
  label: "Google Organic SERP"
  description: "Returns top organic results for a keyword. Live, ~$0.0006/call."
  result_view: serp_table        # custom renderer instead of auto-detect
  default_params:
    location_name: "United Kingdom"
    language_name: "English"

backlinks.backlinks_live:
  hide_fields: [exclude_internal_backlinks]  # rarely useful
  default_params:
    limit: 100
```

Endpoints without an override still work — they just get auto-generated UX.

### 5.4 Task-based endpoints

For `task_post` / `tasks_ready` / `task_get` triplets, the runner abstracts the round-trip:

- User fills a single form, hits Run
- Runner posts the task, stores the `task_id` in session state, polls `tasks_ready` every N seconds
- Streamlit shows a spinner with elapsed time and a Cancel button
- When ready, runner calls `task_get/{id}` and renders normally

This hides the triplet from the user — they just see "endpoint, form, result".

---

## 6. What's possible to add (the long list)

Grouped by impact and effort. The first column is what's already implicitly part of the rebuild; the rest are pickable additions.

### 6.1 Baseline (in the rebuild)

| Feature                            | Why                                                         |
|------------------------------------|-------------------------------------------------------------|
| Auto-generated forms for all 1,130 endpoints | The whole point                                     |
| Endpoint fuzzy search              | Required for navigation at this scale                       |
| Smart result rendering             | Table / chart / tree / JSON depending on shape              |
| Universal CSV + JSON export        | Already partly present, generalise                          |
| Run history (in-session)           | Re-run / load params from recent calls                      |
| Saved presets                      | Named, persisted endpoint+params combos                     |
| BYOK auth (already exists)         | Already in sidebar; add "remember for session"              |
| Task-based endpoint handling       | Required to cover SERP/On-Page properly                     |
| Per-endpoint overrides (YAML)      | Upgrade hot endpoints without abandoning the auto flow      |
| Modular codebase                   | Tests possible, file size shrinks, onboarding gets easier   |

### 6.2 Strong v1 candidates (pickable)

| Feature                       | Why                                                              | Effort     |
|-------------------------------|------------------------------------------------------------------|------------|
| **Cost preview per call**         | DataForSEO charges per call; surface estimated cost before Run.     | Low–medium |
| **Account balance widget**        | Show current credit balance in sidebar (uses `appendix.user_data`).  | Low        |
| **Shareable run URLs**            | Encode endpoint+params in URL query string for Slack-paste links.    | Low        |
| **Result diff between runs**      | "Compare this run to last Tuesday's" for monitoring workflows.       | Medium     |
| **Bulk run from CSV**             | Upload CSV of keywords/domains, runs endpoint for each row.          | Medium     |
| **Scheduled re-runs (cron)**      | Run a preset daily/weekly, store snapshots for trend lines.         | High       |
| **Client workspaces**             | Group presets/history by client (Signature Cashmere, DesiMe, etc.).  | Medium     |
| **Per-endpoint docs panel**       | Embed DataForSEO's official doc text + example response.            | Low        |
| **Dark mode toggle**              | Streamlit theme switcher.                                            | Trivial    |

### 6.3 v2 / later

| Feature                       | Notes                                                              |
|-------------------------------|--------------------------------------------------------------------|
| **Multi-endpoint workflows**      | Chain endpoints: SERP → grab competitor domains → backlinks summary. Likely needs a DAG editor or YAML pipeline format. |
| **LLM-assisted endpoint pick**    | "I want to find sites linking to my competitors but not to me" → suggest endpoint. Uses Claude API, BYOK for that too. |
| **Embedded report templates**     | Pre-built compositions (e.g. "Weekly SEO digest for client X") that run multiple endpoints and assemble a PDF.        |
| **Streamlit → FastAPI swap**      | If the app outgrows Streamlit's reactivity model. Keep optional.    |
| **Multi-user / org**              | Auth, roles, shared presets. Probably belongs in a hosted variant.  |
| **MCP server wrapper**            | Expose the same gateway as an MCP server so Claude Code can drive it directly. Eats your own dog food. |

---

## 7. Open decisions before the spec freezes

| # | Decision needed                                                                 | Default if no input                                |
|---|----------------------------------------------------------------------------------|----------------------------------------------------|
| A | Cost preview per call — in or out of v1?                                         | In (cheap, high-value for credit-conscious users) |
| B | Account balance widget in sidebar?                                               | In (one extra call at startup)                     |
| C | Shareable URL state encoding?                                                    | In (Streamlit supports `st.query_params`)         |
| D | Bulk-from-CSV in v1, or v2?                                                      | v2 (adds form complexity)                          |
| E | Client workspaces for grouping presets?                                          | v2 (presets work without it; can add later)        |
| F | Where do presets/history persist? Session only / local file / SQLite / Postgres? | Local SQLite file (survives restarts, no infra)   |
| G | Per-endpoint overrides — start empty, or seed with the ~30 already polished ones?| Seed with the existing 30                          |
| H | Keep the `app.py` rebuild on a feature branch and ship side-by-side, or in place?| Feature branch, swap when v1 is ready              |

---

## 8. Phased plan

### Phase 0 — Scaffolding (no Streamlit changes yet)

1. Add `dataforseo-client` to `requirements.txt`.
2. Write `registry/introspect.py` — verify we can walk every API module and extract request-model fields. Save the catalogue as JSON for inspection.
3. Acceptance: `python -m seo_analyser.registry.introspect` prints all 1,130 endpoints grouped by family.

### Phase 1 — Generic endpoint runner

1. New `app.py` with the modular layout.
2. Sidebar: creds + family + endpoint picker (no search yet).
3. Form builder for `str / int / bool / List[str] / enum` fields.
4. Runner for live endpoints only.
5. Result tab: raw JSON.
6. Acceptance: pick any live endpoint, fill form, see JSON.

### Phase 2 — Smart results + UX polish

1. Auto-detect result shape, render table / chart / tree.
2. CSV + JSON export buttons on every result.
3. Fuzzy endpoint search in sidebar.
4. Task-based endpoint support (post → poll → get).
5. Acceptance: run `serp.google_organic_live_advanced` and `backlinks.backlinks_live` — see a clean table without writing any custom code.

### Phase 3 — History + presets

1. SQLite store for run history + named presets.
2. Sidebar "Recent runs" and "Presets" sections.
3. Re-run / load-params interactions.
4. Acceptance: run a query, refresh the page, re-run from history.

### Phase 4 — Cost + balance + overrides

1. Account balance widget.
2. Per-call cost preview (from a price table we bake in, or from `appendix.user_data` if it returns prices).
3. Seed `overrides.yml` with the ~30 endpoints already polished today so they keep their bespoke UX.
4. Acceptance: form shows estimated cost before Run; balance updates after.

### Phase 5 — Cutover

1. Update README, Procfile (no change expected), railway.json.
2. Swap `main` branch.
3. Old `app.py` archived to `archive/app_v1.py` for reference.

---

## 9. What this is not

- **Not a DataForSEO competitor.** It's a thin gateway. We do not cache, transform, or re-sell their data.
- **Not multi-user out of the box.** Single operator (you / a client), BYOK. Multi-user is a v2+ topic that probably belongs in a separate hosted variant.
- **Not an SEO insights generator.** The tool surfaces the data; interpretation stays with the user or downstream LLMs.
- **Not a workflow engine in v1.** Multi-endpoint chaining is explicitly v2.

---

## 10. Next steps

1. **Jon reviews this document** and answers the open decisions in section 7.
2. Once locked, I'll convert this into the formal design spec at `docs/superpowers/specs/2026-05-29-seo-analyser-design.md` and commit.
3. Then transition to writing the implementation plan (phased per section 8).
4. Phase 0 can start as soon as the spec is signed off.
