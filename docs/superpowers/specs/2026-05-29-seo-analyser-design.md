# SEO Analyzer Tool — Design Spec

**Status:** Approved design, pre-implementation-plan
**Date:** 2026-05-29
**Author:** Jon Goodey (Indexify)
**Supersedes open decisions in:** `docs/seo-analyser-overview.md` §7

This is the frozen design for the rebuild of "AI Keyword Analyser" into a bring-your-own-key universal gateway over the DataForSEO API. It builds on the three analysis documents in `docs/` (`seo-analyser-overview.md`, `current-app-audit.md`, `sdk-technical-analysis.md`, `endpoint-inventory.md`) and locks the eight open decisions.

---

## 1. Goal

Replace the 3,550-line monolithic `app.py` (which hand-codes ~29 of DataForSEO's 565 endpoints) with a modular Streamlit app that **auto-generates forms for every endpoint** by introspecting the official `dataforseo-client` Python SDK. Stay on Streamlit + Railway. Keep BYOK auth.

Success = a user can pick any of the 565 endpoints from a searchable sidebar, fill an auto-generated form, run it (live or task-based), see a smartly-rendered result, export it, and find it again in run history.

---

## 2. Locked decisions

From `seo-analyser-overview.md` §4 (already locked) plus §7 (resolved here):

| # | Decision | Choice |
|---|----------|--------|
| 1 | Endpoint strategy | Auto-generated forms from SDK introspection |
| 2 | Spec source | Official `dataforseo-client` PythonClient SDK |
| 3 | Migration path | **Feature branch `rebuild/seo-analyser`**, swap at cutover |
| 4 | Results presentation | Smart auto-detection (table / chart / tree / raw JSON) |
| 5 | v1 personal feature | Run history + saved presets |
| 6 | Product name | "SEO Analyzer Tool" |
| A | Cost preview per call | **In v1** |
| B | Account balance widget | **In v1** |
| C | Shareable run URLs | **In v1** |
| D | Bulk run from CSV | **In v1** |
| E | Client workspaces | **v2** (but add nullable `workspace` column now to avoid later migration) |
| F | Persistence layer | **Postgres** (Railway), with in-memory fallback when no `DATABASE_URL` |
| G | overrides.yml seeding | **Seed with the existing ~29** so known tools don't regress |
| H | Migration path detail | Build on branch, archive `app.py` to `archive/app_v1.py` at Phase 5 |

Baselines treated as non-optional: endpoint fuzzy search, universal CSV/JSON export, BYOK sidebar auth.

---

## 3. Architecture

### 3.1 Module layout

```
ai-overviews/
├── app.py                          # thin entrypoint -> seo_analyser.ui.app:main()
├── seo_analyser/
│   ├── __init__.py
│   ├── auth.py                     # credentials + session state; reads .env.local for dev
│   ├── registry/
│   │   ├── introspect.py           # walk dataforseo_client.api.*, extract methods + request models
│   │   ├── catalogue.py            # cached catalogue {family: [endpoint meta]}, JSON-backed
│   │   └── overrides.yml           # per-endpoint UX hints (seeded with the 29)
│   ├── forms/
│   │   ├── builder.py              # request model -> Streamlit widgets
│   │   ├── widgets.py              # type -> widget mapping; enum/range extraction from descriptions
│   │   └── validators.py           # client-side checks before submit
│   ├── runner/
│   │   ├── live.py                 # execute live endpoints
│   │   ├── tasks.py                # post -> poll tasks_ready -> task_get_* flow
│   │   └── errors.py               # normalise SDK exceptions to typed app errors
│   ├── results/
│   │   ├── detect.py               # shape detection: list[dict]->table, timeseries->chart, etc.
│   │   ├── renderers.py            # plotly + st.dataframe + nested JSON viewer
│   │   └── export.py               # CSV / JSON download buttons
│   ├── billing/
│   │   └── cost.py                 # estimate $ per call from description $-hints + baked price table
│   ├── persistence/
│   │   └── db.py                   # SQLAlchemy engine; DATABASE_URL or in-memory fallback; schema
│   ├── history/
│   │   ├── store.py                # runs repository
│   │   └── presets.py              # presets repository
│   └── ui/
│       ├── app.py                  # main() — wires sidebar + page
│       ├── sidebar.py              # creds, search, family/endpoint picker, balance widget, bulk-CSV
│       ├── share.py                # encode/decode endpoint+params <-> st.query_params
│       ├── endpoint_page.py        # form + run + results + cost preview
│       └── home.py                 # landing, recent runs, presets
├── tests/
│   ├── test_introspect.py
│   ├── test_form_builder.py
│   ├── test_result_detect.py
│   ├── test_cost.py
│   └── test_persistence.py         # runs against in-memory fallback
├── archive/app_v1.py               # the old monolith (added at Phase 5)
├── requirements.txt                # + dataforseo-client, pydantic>=2, sqlalchemy, psycopg[binary]
├── Procfile
├── railway.json
└── docs/ ...
```

### 3.2 Core flow

1. **Introspection** (cached at startup): walk every class in `dataforseo_client.api.*`, list public methods, drop `_with_http_info` / `_without_preload_content` variants, pull the request-model class from each method's type hint, extract `model_fields` (name, annotation, description, default).
2. **Catalogue**: `{family: [{name, http_path, request_model, fields, is_task_based, task_methods}, ...]}`, persisted to `catalogue.json`, rebuilt only on SDK version change.
3. **Sidebar**: family + endpoint pickers from the catalogue, plus a fuzzy search box across endpoint names/paths. Balance widget at top (one `appendix/user_data` call, cached). Optional bulk-CSV uploader.
4. **Form builder**: per-field widget from the type→widget table (§3.3). Help text from `FieldInfo.description`. Enum/range parsed from description prose where present. Nested models behind an "Advanced" expander in v1.
5. **Cost preview**: before Run, estimate cost from the baked price table keyed by family/endpoint, surfaced as a caption near the Run button.
6. **Runner**: instantiate the SDK Api class with current creds; live endpoints return immediately; task-based endpoints post → store `task_id` in `st.session_state` → poll `tasks_ready` every 5s with spinner + elapsed + Cancel → `task_get_advanced`.
7. **Results detector**: pick a renderer by response shape; raw JSON always available as a fallback tab. Distinguish "empty data" (`items: []`) from "error".
8. **History**: each run writes to Postgres (or in-memory); "Re-run" loads params back into the form. Shareable URL encodes endpoint+params into `st.query_params`.

### 3.3 Type → widget mapping

Per `sdk-technical-analysis.md` §6 (authoritative):

| Pydantic type | Widget |
|---------------|--------|
| `Optional[StrictStr]` | `st.text_input`; `st.selectbox` if description lists "possible values: a, b, c" |
| `Optional[StrictInt]` | `st.number_input(min, max, step=1)`, range parsed from description |
| `Optional[StrictFloat]` | `st.number_input(format="%.4f")` or `st.slider` for bounded floats |
| `Optional[StrictBool]` | `st.checkbox`, default from `FieldInfo.default` |
| `Optional[List[StrictStr/Int]]` | `st.text_area` split on newlines/commas |
| `Optional[List[NestedModel]]` | recursive sub-form behind "Advanced" expander |
| date-like field name | `st.date_input` → ISO string |

Enum extraction regex (`r"possible values:?\s*([a-z_, ]+)"`) covers ~80%; the rest stay free-text. Same approach for ranges (`max value: N`, `range: A-B`, `from A to B`).

### 3.4 Persistence

`persistence/db.py` exposes `get_engine()`:
- If `DATABASE_URL` is set → SQLAlchemy engine over Railway Postgres via `psycopg`.
- Else → in-memory store (a module-level dict-backed shim implementing the same repository interface), so local dev and tests need no DB.

Schema (SQLAlchemy Core, created on first connect):

```
runs(
  id, endpoint TEXT, family TEXT, params JSONB, cost NUMERIC,
  response_bytes INT, status TEXT, created_at TIMESTAMPTZ, workspace TEXT NULL
)
presets(
  id, name TEXT, endpoint TEXT, params JSONB, created_at TIMESTAMPTZ, workspace TEXT NULL
)
```

`workspace` is nullable and unused in v1 — present so v2 client workspaces need no migration.

### 3.5 Error handling

The SDK raises typed exceptions (`ApiException` etc.). `runner/errors.py` normalises these to an app-level `RunError(kind, message, status_code)` with kinds `auth | rate_limit | bad_request | server | network | empty`. The UI catches `RunError` and renders an appropriate message. **No `st.*` calls inside runner/registry/persistence** — those layers stay UI-free and unit-testable.

---

## 4. Testing strategy

- `test_introspect.py` — catalogue builds, 565 endpoints, families match the inventory, request models resolve.
- `test_form_builder.py` — each Pydantic type maps to the expected widget spec; enum/range extraction on sample descriptions.
- `test_result_detect.py` — sample responses route to the correct renderer; empty vs error distinguished.
- `test_cost.py` — price-table lookups and description $-hint parsing.
- `test_persistence.py` — runs against the in-memory fallback (no DB needed in CI).

UI layers (`ui/`, `forms/widgets.py` rendering) are smoke-tested manually per phase acceptance, not unit-tested, because Streamlit widgets are hard to assert on. The form *builder* (which produces widget specs) IS unit-tested; the rendering of those specs is not.

---

## 5. Build phases

Built on branch `rebuild/seo-analyser`. Each phase ends with a runnable acceptance check.

### Phase 0 — SDK spike (de-risk)

The whole design rests on the SDK introspecting as predicted. Verify before building anything.

1. Add `dataforseo-client`, `pydantic>=2` to `requirements.txt`; create a venv; install.
2. Implement `registry/introspect.py` per `sdk-technical-analysis.md` §9.
3. Dump `catalogue.json`.

**Acceptance:** `python -m seo_analyser.registry.introspect` prints all families with endpoint counts matching `endpoint-inventory.md` (565 total), and at least one request model's fields (names + descriptions) are extracted correctly. If counts diverge materially, stop and revise the design.

### Phase 1 — Generic live runner

1. Modular skeleton + thin `app.py`.
2. `auth.py` (creds from sidebar + `.env.local` for dev).
3. Sidebar: family + endpoint picker (no search yet).
4. `forms/builder.py` for `str / int / bool / float / List[str] / enum`.
5. `runner/live.py`; result tab = raw JSON.

**Acceptance:** pick any live endpoint, fill the form, see JSON.

### Phase 2 — Smart results + UX

1. `results/detect.py` + `renderers.py`: table / chart / tree.
2. `results/export.py`: CSV + JSON buttons on every result.
3. Fuzzy endpoint search in sidebar.
4. `runner/tasks.py`: post → poll → get with spinner/cancel.

**Acceptance:** run `serp.google_organic_live_advanced` (live) and one task-based endpoint; both render a clean table with no endpoint-specific code.

### Phase 3 — Persistence

1. `persistence/db.py` (Postgres or in-memory fallback).
2. `history/store.py` + `presets.py`.
3. Sidebar "Recent runs" + "Presets"; re-run / load-params.

**Acceptance:** run a query, restart the app (with `DATABASE_URL` set), re-run from history.

### Phase 4 — Cost, balance, share, bulk, overrides

1. `billing/cost.py` + cost preview near Run.
2. Balance widget (`appendix/user_data`).
3. `ui/share.py` shareable URLs via `st.query_params`.
4. Bulk-CSV: upload rows, run endpoint per row, aggregate results.
5. Seed `registry/overrides.yml` with the 29 endpoints from `current-app-audit.md` §3.1 (labels, defaults, custom chart hints).

**Acceptance:** form shows estimated cost before Run; balance shows in sidebar; a run produces a shareable URL that reloads its params; a small CSV runs N rows; the 29 known endpoints keep polished labels/charts.

### Phase 5 — Cutover

1. `app.py` → `archive/app_v1.py`; new thin `app.py` becomes the entrypoint.
2. Update README, Procfile (likely unchanged), `railway.json`; document `DATABASE_URL`.
3. Remove the stray empty `no data - warning message...` file; add `__pycache__` to `.gitignore`.
4. Merge `rebuild/seo-analyser` → `main`.

**Acceptance:** Railway deploys the rebuilt app; `main` runs the new entrypoint; old app preserved in `archive/`.

---

## 6. Out of scope (v2+)

Per `seo-analyser-overview.md` §6.3 and decision E: client workspaces, multi-endpoint workflows/DAG, LLM-assisted endpoint pick, embedded report templates, FastAPI swap, multi-user/org, MCP server wrapper. None of these are built in v1; the only v1 concession to v2 is the nullable `workspace` column.

---

## 7. Risks (carried from `sdk-technical-analysis.md` §10)

| Risk | Mitigation |
|------|------------|
| SDK doesn't introspect as predicted | Phase 0 spike gates everything |
| Description prose inconsistent for enum/range | Partial extraction; free-text fallback |
| Nested models make wide forms | "Advanced" expander; override hooks |
| Task polling adds Streamlit rerun complexity | Dedicated `runner/tasks.py` component, spinner + cancel |
| Railway FS ephemeral | Postgres add-on; in-memory fallback locally |
| SDK version drift | Pin version in requirements; surface version in sidebar |

---

## 8. Cross-references

- Strategy + original architecture: `docs/seo-analyser-overview.md`
- Current app audit: `docs/current-app-audit.md`
- SDK feasibility: `docs/sdk-technical-analysis.md`
- Endpoint inventory + v1 tiers: `docs/endpoint-inventory.md`
