# SEO Analyzer Tool — Phases 2–5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the working Phase 0–1 gateway (auto-generated forms + live runner, now with smart result tables, friendly labels, required/optional markers, model dropdowns and location/language presets) through to a feature-complete, deployable v1.

**Architecture:** Keep the modular `seo_analyser/` package and Streamlit + Railway. Add global search, universal export, task-based endpoint polling, durable persistence (Postgres with in-memory fallback), and the remaining v1 features, then cut over from `app.py` to the rebuild.

**Tech Stack:** Python 3.13, Streamlit 1.32, dataforseo-client 2.0.25, Pydantic v2, SQLAlchemy + psycopg, pytest.

**Branch:** continue on `rebuild/seo-analyser`.

**Spec:** `docs/superpowers/specs/2026-05-29-seo-analyser-design.md`.

---

## Already done (Phases 0–1 + early Phase 2)

So the executing engineer does not redo these:

- SDK introspection catalogue (565 endpoints), live runner, auto-generated forms.
- Smart result rendering: status/results/cost metrics, scalar table, LLM/AI answer text, raw-JSON expander (`results/detect.py`, `results/render.py`).
- Friendly labels + common/advanced split + required/conditional/optional/default markers (`labels.py`, `forms/widgets.py`, `forms/builder.py`).
- `model_name` dropdowns from the sibling `*_models` endpoint (`runner/lookups.py`); tri-state booleans; `additional_properties` excluded.
- Location/language quick-pick presets with free-text fallback (`presets.py`).
- First-load catalogue spinner.

**Tests:** 37 passing. **Entry point:** `app_v2.py` on port 8501.

---

## Phase 2 — Navigation, export, task-based endpoints

### File structure (Phase 2)

| File | Responsibility |
|------|----------------|
| `seo_analyser/registry/catalogue.py` (modify) | add `all_endpoints`, `search_endpoints`, `matches_query` |
| `seo_analyser/registry/introspect.py` (modify) | classify endpoints (live/task/support); group task triplets |
| `seo_analyser/results/export.py` (create) | CSV + JSON serialisation of results |
| `seo_analyser/results/render.py` (modify) | add CSV/JSON download buttons |
| `seo_analyser/runner/tasks.py` (create) | post → poll → get flow for task endpoints |
| `seo_analyser/ui/sidebar.py` (modify) | global endpoint search box |
| `seo_analyser/ui/endpoint_page.py` (modify) | route task endpoints to the task runner |
| `tests/test_search.py`, `tests/test_export.py`, `tests/test_tasks.py` (create) | unit tests |

---

### Task 1: Global endpoint search

**Files:**
- Modify: `seo_analyser/registry/catalogue.py`
- Test: `tests/test_search.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_search.py
from seo_analyser.registry.catalogue import matches_query


def test_matches_all_tokens():
    assert matches_query("serp", "google_organic_live_advanced", "google organic") is True
    assert matches_query("serp", "google_organic_live_advanced", "organic serp") is True


def test_non_match():
    assert matches_query("serp", "google_organic_live_advanced", "backlinks") is False


def test_empty_query_is_false():
    assert matches_query("serp", "google_organic_live_advanced", "") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_search.py -v`
Expected: FAIL — `ImportError: cannot import name 'matches_query'`

- [ ] **Step 3: Implement in `catalogue.py`**

Append:
```python
def all_endpoints() -> list[EndpointMeta]:
    out: list[EndpointMeta] = []
    for eps in get_catalogue().values():
        out.extend(eps)
    return out


def matches_query(family: str, name: str, query: str) -> bool:
    q = query.lower().split()
    if not q:
        return False
    haystack = f"{family} {name}".lower()
    return all(token in haystack for token in q)


def search_endpoints(query: str, limit: int = 50) -> list[EndpointMeta]:
    hits = [e for e in all_endpoints() if matches_query(e.family, e.name, query)]
    return hits[:limit]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_search.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Wire into the sidebar**

In `seo_analyser/ui/sidebar.py`, replace the body of `render_sidebar` with a search-first flow:
```python
"""Sidebar: credentials + endpoint search / family+endpoint picker."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials, from_env
from seo_analyser.labels import titleize
from seo_analyser.registry import catalogue


def render_sidebar() -> tuple[Credentials, str | None, str | None]:
    env = from_env()
    with st.sidebar:
        st.header("DataForSEO credentials")
        login = st.text_input("Login", value=env.login)
        password = st.text_input("Password", value=env.password, type="password")
        creds = Credentials(login=login, password=password)
        if creds.is_complete:
            st.caption("✓ Credentials loaded")

        st.header("Choose an endpoint")
        query = st.text_input("Search all endpoints", placeholder="e.g. ai overview, backlinks")
        if query.strip():
            hits = catalogue.search_endpoints(query)
            if not hits:
                st.caption("No endpoints match.")
                return creds, None, None
            labels = {f"{titleize(e.family)} · {titleize(e.name)}": (e.family, e.name) for e in hits}
            chosen = st.selectbox(f"{len(hits)} matches", list(labels))
            family, endpoint_name = labels[chosen]
            return creds, family, endpoint_name

        family = st.selectbox("API family", catalogue.families(), format_func=titleize)
        endpoints = catalogue.endpoints_for(family)
        names = [e.name for e in endpoints]
        endpoint_name = st.selectbox("Endpoint", names, format_func=titleize) if names else None
        st.caption(f"{len(names)} endpoints in {titleize(family)}")
    return creds, family, endpoint_name
```

- [ ] **Step 6: Smoke-test**

Run: `streamlit run app_v2.py --server.port 8501`
Type "ai overview" in the search box; confirm matching endpoints across families appear and selecting one renders its form.

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/registry/catalogue.py seo_analyser/ui/sidebar.py tests/test_search.py
git commit -m "feat: global fuzzy endpoint search in sidebar"
```

---

### Task 2: CSV + JSON export

**Files:**
- Create: `seo_analyser/results/export.py`
- Modify: `seo_analyser/results/render.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_export.py
import json

from seo_analyser.results.export import to_csv_bytes, to_json_bytes


def test_to_csv_bytes_has_header_and_rows():
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    text = to_csv_bytes(rows).decode("utf-8")
    assert "a,b" in text.splitlines()[0]
    assert "1,x" in text


def test_to_csv_empty():
    assert to_csv_bytes([]) == b""


def test_to_json_bytes_roundtrips():
    payload = {"status_code": 20000, "tasks": [{"id": "1"}]}
    assert json.loads(to_json_bytes(payload)) == payload
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_export.py -v`
Expected: FAIL — `ModuleNotFoundError: seo_analyser.results.export`

- [ ] **Step 3: Implement `export.py`**

```python
"""Serialise results to CSV / JSON bytes for download."""
from __future__ import annotations

import csv
import io
import json


def to_csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def to_json_bytes(payload) -> bytes:
    return json.dumps(payload, indent=2, default=str).encode("utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_export.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Add download buttons to the renderer**

In `seo_analyser/results/render.py`, add the import and a download row after the table. Insert at the top with the other imports:
```python
from datetime import datetime

from seo_analyser.results.export import to_csv_bytes, to_json_bytes
```
Then change the `render_result` signature to accept the endpoint name, and add buttons. Replace the function definition line:
```python
def render_result(resp: dict, endpoint: str = "result") -> None:
```
and immediately before the final `with st.expander("Raw JSON response"):` add:
```python
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    col_csv, col_json = st.columns(2)
    if rows:
        col_csv.download_button(
            "Download CSV", to_csv_bytes(rows),
            file_name=f"{endpoint}-{stamp}.csv", mime="text/csv",
        )
    col_json.download_button(
        "Download JSON", to_json_bytes(resp),
        file_name=f"{endpoint}-{stamp}.json", mime="application/json",
    )
```

- [ ] **Step 6: Pass the endpoint name from the page**

In `seo_analyser/ui/endpoint_page.py`, update the success call:
```python
        render_result(result, endpoint=endpoint_name)
```

- [ ] **Step 7: Smoke-test**

Run the app, run any live endpoint, confirm "Download CSV" and "Download JSON" buttons appear and download non-empty files.

- [ ] **Step 8: Commit**

```bash
git add seo_analyser/results/export.py seo_analyser/results/render.py seo_analyser/ui/endpoint_page.py tests/test_export.py
git commit -m "feat: universal CSV + JSON export on results"
```

---

### Task 3: Classify endpoints and collapse task triplets

Goal: in the catalogue, present `{base}_task_post` + `{base}_tasks_ready` + `{base}_task_get_*` as ONE logical task endpoint, and tag each endpoint as `live` / `task` / `support`, so the dropdown stops showing four entries per task operation.

**Files:**
- Modify: `seo_analyser/registry/introspect.py`
- Test: `tests/test_tasks.py` (classification portion)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tasks.py
from seo_analyser.registry.introspect import group_task_methods


def test_groups_triplet():
    methods = [
        "google_organic_live_advanced",
        "google_organic_task_post",
        "google_organic_tasks_ready",
        "google_organic_task_get_advanced",
        "google_organic_task_get_regular",
    ]
    groups = group_task_methods(methods)
    assert "google_organic" in groups
    g = groups["google_organic"]
    assert g["post"] == "google_organic_task_post"
    assert g["ready"] == "google_organic_tasks_ready"
    assert g["get"] == "google_organic_task_get_advanced"   # prefers advanced


def test_no_post_means_no_group():
    assert group_task_methods(["serp_locations"]) == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tasks.py -v`
Expected: FAIL — `cannot import name 'group_task_methods'`

- [ ] **Step 3: Implement grouping in `introspect.py`**

Add near the top:
```python
def group_task_methods(method_names: list[str]) -> dict[str, dict[str, str]]:
    """Group {base}_task_post/_tasks_ready/_task_get_* triplets by base name."""
    names = set(method_names)
    groups: dict[str, dict[str, str]] = {}
    for name in method_names:
        if not name.endswith("_task_post"):
            continue
        base = name[: -len("_task_post")]
        ready = f"{base}_tasks_ready"
        get = None
        for suffix in ("_task_get_advanced", "_task_get_regular", "_task_get_html", "_task_get"):
            if f"{base}{suffix}" in names:
                get = f"{base}{suffix}"
                break
        groups[base] = {
            "post": name,
            "ready": ready if ready in names else "",
            "get": get or "",
        }
    return groups
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tasks.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Extend `EndpointMeta` and `build_catalogue`**

Add fields to `EndpointMeta` (keep existing fields):
```python
@dataclass(frozen=True)
class EndpointMeta:
    name: str
    family: str
    request_model: type | None
    is_task_based: bool
    kind: str = "live"                 # "live" | "task" | "support"
    task_methods: tuple = ()           # (post, ready, get) for kind == "task"
```

In `build_catalogue`, after collecting `endpoints` for a family, fold the triplets. Replace the per-family append loop's result handling with:
```python
        all_method_names = [e.name for e in endpoints]
        groups = group_task_methods(all_method_names)
        grouped_members = set()
        for base, g in groups.items():
            for role in ("post", "ready", "get"):
                if g[role]:
                    grouped_members.add(g[role])

        folded: list[EndpointMeta] = []
        for e in endpoints:
            if e.name in grouped_members and not e.name.endswith("_task_post"):
                continue  # absorbed into the task endpoint
            if e.name.endswith("_task_post"):
                base = e.name[: -len("_task_post")]
                g = groups[base]
                folded.append(EndpointMeta(
                    name=base, family=family, request_model=e.request_model,
                    is_task_based=True, kind="task",
                    task_methods=(g["post"], g["ready"], g["get"]),
                ))
            else:
                folded.append(e)
        catalogue[family] = folded
```
(Remove the previous `catalogue[family] = endpoints` line.)

- [ ] **Step 6: Run all tests**

Run: `pytest tests/test_introspect.py tests/test_tasks.py -v`
Expected: PASS. Note `test_serp_is_largest_family` still holds (folding reduces counts but SERP stays largest). If `test_task_based_detection` relied on `_task_post` names, update it to assert `any(e.kind == "task" for e in CATALOGUE["serp"])`.

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/registry/introspect.py tests/test_tasks.py tests/test_introspect.py
git commit -m "feat: classify endpoints and collapse task triplets into one logical endpoint"
```

---

### Task 4: Task-based runner with polling

**Files:**
- Create: `seo_analyser/runner/tasks.py`
- Modify: `seo_analyser/ui/endpoint_page.py`
- Test: `tests/test_tasks.py` (add task-id extraction test)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tasks.py`:
```python
from seo_analyser.runner.tasks import extract_task_id, ready_ids


def test_extract_task_id():
    resp = {"tasks": [{"id": "abc-123", "status_code": 20100}]}
    assert extract_task_id(resp) == "abc-123"


def test_extract_task_id_missing():
    assert extract_task_id({"tasks": []}) is None


def test_ready_ids():
    resp = {"tasks": [{"result": [{"id": "a"}, {"id": "b"}]}]}
    assert ready_ids(resp) == {"a", "b"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tasks.py -v`
Expected: FAIL — `ModuleNotFoundError: seo_analyser.runner.tasks`

- [ ] **Step 3: Implement `tasks.py`**

```python
"""Run task-based endpoints: post -> poll tasks_ready -> fetch by id."""
from __future__ import annotations

import time

from seo_analyser.auth import Credentials
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.runner.errors import RunError, normalise
from seo_analyser.runner.live import _api_class_for, _to_dict


def extract_task_id(resp: dict) -> str | None:
    tasks = resp.get("tasks") or []
    if not tasks:
        return None
    return tasks[0].get("id")


def ready_ids(resp: dict) -> set[str]:
    out: set[str] = set()
    for task in resp.get("tasks") or []:
        for row in task.get("result") or []:
            if isinstance(row, dict) and row.get("id"):
                out.add(row["id"])
    return out


def run_task(meta: EndpointMeta, payload: dict, creds: Credentials,
             on_wait=None, max_wait: int = 120, interval: int = 5) -> dict:
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    post_method, ready_method, get_method = meta.task_methods
    if not (post_method and ready_method and get_method):
        raise RunError("bad_request", f"{meta.name} is missing task methods.")

    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    conf = cfg.Configuration(username=creds.login, password=creds.password)
    try:
        request_obj = meta.request_model(**payload)
        with prov.ApiClient(conf) as client:
            api = _api_class_for(meta.family)(client)
            posted = _to_dict(getattr(api, post_method)([request_obj]))
            task_id = extract_task_id(posted)
            if not task_id:
                raise RunError("bad_request", f"Task not accepted: {posted.get('status_message')}")

            waited = 0
            while waited < max_wait:
                ready = _to_dict(getattr(api, ready_method)())
                if task_id in ready_ids(ready):
                    break
                if on_wait:
                    on_wait(waited)
                time.sleep(interval)
                waited += interval

            return _to_dict(getattr(api, get_method)(id=task_id))
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise normalise(exc) from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tasks.py -v`
Expected: PASS (all task tests)

- [ ] **Step 5: Route task endpoints in the page**

In `seo_analyser/ui/endpoint_page.py`, add the import:
```python
from seo_analyser.runner.tasks import run_task
```
Replace the task-based `st.info(...)` block and the Run handler so task endpoints poll. Replace the Run button block with:
```python
    if st.button("Run", type="primary"):
        if "model_name" in dynamic_choices and not payload.get("model_name"):
            st.warning("Please choose a model from the dropdown before running.")
            return
        try:
            if meta.kind == "task":
                with st.spinner("Task submitted — polling for results (up to ~2 min)..."):
                    result = run_task(meta, payload, creds)
            else:
                with st.spinner("Calling DataForSEO..."):
                    result = run_live(meta, payload, creds)
        except RunError as err:
            st.error(str(err))
            return
        render_result(result, endpoint=endpoint_name)
```
And delete the earlier `if meta.is_task_based: st.info(...)` notice (task endpoints now work).

- [ ] **Step 6: Smoke-test**

Run the app, pick a task endpoint (e.g. On-Page `task_post` based crawl, or a SERP task endpoint), submit, confirm the spinner shows and results render after polling.

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/runner/tasks.py seo_analyser/ui/endpoint_page.py tests/test_tasks.py
git commit -m "feat: task-based endpoint polling (post -> ready -> get)"
```

---

### Phase 2 acceptance

- Search "ai overview" surfaces matching endpoints across families.
- Any result offers CSV + JSON download.
- Task endpoints appear once (not as 4 triplet entries) and run via polling.
- Full suite green: `pytest -q`.

---

## Phase 3 — Persistence (history + saved presets)

> Detailed task breakdown to be written as its own plan once Phase 2 lands; scope and key decisions fixed here.

**Goal:** Durable run history and named presets, per the spec's Postgres-with-in-memory-fallback decision.

**File structure:** `seo_analyser/persistence/db.py` (engine: `DATABASE_URL` → Postgres via psycopg, else in-memory shim implementing the same repository interface), `seo_analyser/history/store.py` (runs repo), `seo_analyser/history/presets.py` (presets repo), `seo_analyser/ui/home.py` (Recent runs + Presets), wire into `ui/app.py` and `ui/endpoint_page.py`.

**Schema:** `runs(id, endpoint, family, params JSONB, cost, response_bytes, status, created_at, workspace NULL)`; `presets(id, name, endpoint, params JSONB, created_at, workspace NULL)`. `workspace` nullable now to avoid a v2 migration.

**Key tasks:** (1) `persistence/db.py` with engine selection + schema creation, tested against the in-memory fallback; (2) repositories with `add_run`/`recent_runs` and `save_preset`/`list_presets`/`load_preset`; (3) record each run after `render_result`; (4) sidebar/home "Recent runs" + "Presets" with re-run/load-params (writes params back into `st.session_state` form keys); (5) `requirements.txt` += `sqlalchemy`, `psycopg[binary]`.

**Acceptance:** run a query, restart with `DATABASE_URL` set, re-run from history; tests pass against in-memory fallback (no DB needed in CI).

---

## Phase 4 — Cost, balance, shareable URLs, bulk-CSV, overrides

> Detailed task breakdown to be written as its own plan; scope fixed here. All four pickable features were locked into v1.

**Goal:** surface cost before running, show account balance, make runs shareable, support bulk input, and preserve the 29 polished endpoints.

**Key tasks:**
1. **Cost preview** — `billing/cost.py` with a baked per-family price table (seed from `endpoint-inventory.md` §17) plus `extract_cost_hint` parsing "$0.00x" from field descriptions; show an estimate caption by the Run button. Tested pure.
2. **Account balance widget** — call `appendix` `user_data`; show remaining balance in the sidebar (cached per session). Tested via parser on a sample `user_data` response.
3. **Shareable URLs** — `ui/share.py` encode/decode `{family, endpoint, params}` to/from `st.query_params`; on load, prefill the form; a "Copy shareable link" control. Pure encode/decode tested.
4. **Bulk-from-CSV** — uploader that maps CSV columns to a chosen field (e.g. `keyword`), runs the endpoint per row, concatenates results into one table; cap + `log` dropped rows. Pure row→payload mapping tested.
5. **Seed `registry/overrides.yml`** — for the 29 currently-wired endpoints (see `current-app-audit.md` §3.1): friendly labels, sensible default params (e.g. UK/English), and any custom result hints; loader merges overrides onto auto-generated specs.

**Acceptance:** estimated cost shows before Run; balance shows in sidebar; a run produces a link that reloads its params; a small CSV runs N rows; the 29 endpoints keep polished UX.

---

## Phase 5 — Cutover

> Detailed task breakdown to be written as its own plan; scope fixed here.

**Key tasks:** (1) pin runtime to Python 3.13 for Railway (`runtime.txt` = `python-3.13` or nixpacks config) — **critical**, 3.14 breaks Streamlit/protobuf; (2) `app.py` → `archive/app_v1.py`, rename `app_v2.py` → `app.py`, update `Procfile`; (3) provision Railway Postgres, set `DATABASE_URL`; (4) regenerate `README.md` from the new architecture; (5) remove the stray `no data - warning message...` file; (6) merge `rebuild/seo-analyser` → `main` and verify the Railway deploy.

**Acceptance:** Railway runs the rebuilt app on Python 3.13 with persistence; `main` is the new entry point; old app archived.

---

## Self-review

- **Spec coverage:** Phase 2 covers spec §5 search/export/task-polling; Phases 3–5 map 1:1 to spec phases 3–5 and decisions A–H. Smart rendering (spec Phase 2) already shipped.
- **Polish items from testing folded in:** task-triplet collapse (Task 3), search (Task 1); enum-coverage gaps and first-load latency are noted but deferred (latency is dominated by the unavoidable SDK import; mitigated by the existing spinner).
- **Type consistency:** `EndpointMeta` gains `kind` + `task_methods` (Task 3) and both are consumed in Task 4 (`meta.kind`, `meta.task_methods`) and the page router. `render_result(resp, endpoint)` signature change (Task 2) is applied at its only call site (Task 2 Step 6 / Task 4 Step 5). `to_csv_bytes`/`to_json_bytes`, `matches_query`/`search_endpoints`, `extract_task_id`/`ready_ids`/`run_task` are each defined once and used consistently.
- **No placeholders in Phase 2 tasks.** Phases 3–5 are intentionally roadmap-level (each becomes its own detailed plan), not placeholder bite-sized tasks, because their concrete code depends on Phase 2 outcomes and further SDK/Postgres probing.
