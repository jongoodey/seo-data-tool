# Junior-SEO UX Improvements — Handover & Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SEO Analyzer usable by a first-time junior SEO: stop it burning money on obvious mistakes, translate API errors into plain English, fix the broken-feeling search, and replace the dead-end default page with a task-shaped landing page.

**Architecture:** All changes are inside the existing `seo_analyser` package (Streamlit UI over an auto-generated DataForSEO catalogue). No new dependencies. Pure logic goes in non-Streamlit modules with unit tests; Streamlit rendering is verified manually in the browser.

**Tech Stack:** Python 3.13, Streamlit 1.32, Pydantic (via `dataforseo-client` SDK), SQLAlchemy (SQLite local / Postgres on Railway), pytest.

---

## 0. Read this first (handover context)

You are picking up a live, deployed project with zero shared conversation history. Everything you need is written down:

- **Repo:** `~/Sites/tools/ai-overviews` (remote `origin` = github.com/jongoodey/seo-data-tool). Work on `main` or a worktree branched from it.
- **Read `docs/PROJECT-STATUS.md` before anything else.** It is the living working doc: how to run, test, architecture, decisions, gotchas, session log. Keep it updated.
- **Setup:** `python3.13 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Python 3.13 is mandatory (3.14 breaks Streamlit/protobuf).
- **Run:** `streamlit run app.py --server.port 8501`. Credentials come from `.env.local` (`user_name` / `password`) or the sidebar.
- **Test:** `python -m pytest -q` — 88 tests, all passing at handover (commit `d1d6e93`).
- **Production:** https://seo-data-tool.up.railway.app — **pushing to `main` auto-deploys via Railway.** Do not push until all tasks are done, tests pass, and Jon has given the go-ahead. Verify the live site after deploying.
- **Cost awareness:** every Run is a real, billed DataForSEO call (typically $0.002–$0.01). Keep test spend to a few cents; prefer the cheap SERP endpoint (keyword "indexify", location "United Kingdom", language "English").
- **Style:** Jon prefers British English in UI copy and never uses em-dashes. Match the existing code style (focused modules, docstrings explaining *why*, tests per module).

### Why this work exists (the UX audit, 2026-06-10)

A first-time-user walkthrough of the live app found the experience hostile to a junior SEO even though the underlying tool is strong:

1. **Real bug — premature "Task Not Found".** Task-based endpoints (e.g. ChatGPT LLM Responses) poll `tasks_ready` for 2 minutes then call `task_get` regardless (`seo_analyser/runner/tasks.py:50-60`). LLM tasks routinely take longer, so DataForSEO replies "Task Not Found" for a task that is still running. The user is charged, the task id is thrown away, and the result is never seen.
2. **Money burned on obvious mistakes.** Clicking Run with an empty form makes the paid call anyway and returns `Invalid Field: 'keyword'`, even though the form labelled the field "required". Same trap with `language_name` (a conditional one-of-a-pair field): the API's "Invalid Field" actually means *missing*, which reads as "the tool is broken".
3. **Search betrays its own placeholder.** The sidebar suggests searching "ai overview" but `search_endpoints` is an unranked all-tokens-substring match (`seo_analyser/registry/catalogue.py:33-43`), so "ai" matches the "ai" inside "av**ai**lable"/"dom**ai**n" and the wrong endpoints surface first.
4. **Dead-end landing.** The sidebar auto-selects the first family/endpoint alphabetically, so the very first screen a new user sees is "AI Keyword Data Available Filters — this endpoint takes no inputs and isn't runnable yet".
5. **API vocabulary everywhere.** Family names like "Dataforseo Labs" assume the user already knows the DataForSEO API; nothing maps jobs ("check rankings", "audit a page") to endpoints. Location/language *codes* clutter forms when names are enough, and language is never defaulted.

Jon approved implementing all of it ("implement the lot, make it more user friendly from the junior SEO perspective").

### Known constraints (do not relearn these)

- **"required field" labels in SDK descriptions are unreliable**: many mean "required unless partner field set". `extract_requirement` in `seo_analyser/forms/widgets.py:36-50` already classifies those as `"conditional"` with a `partner`. Blocking is only safe for `requirement == "required"`; never hard-block conditionals individually (only as a pair, see Task 3).
- **`st.status` cannot nest inside `st.expander`** (StreamlitAPIException). Use `st.spinner` plus a session-state outcome message across reruns — see `_start_prereq` in `seo_analyser/ui/endpoint_page.py:163-195` for the working pattern.
- The endpoint catalogue takes ~10s to build on first import (the test suite already pays this once).

---

## File structure (what you will touch)

| File | Change |
|---|---|
| `seo_analyser/runner/errors.py` | `RunError` gains optional `task_id` |
| `seo_analyser/runner/tasks.py` | Pending-task detection; new `fetch_task()` |
| `seo_analyser/persistence/store.py` | New `update_run()` |
| `seo_analyser/results/detect.py` | New `friendly_error()` translator |
| `seo_analyser/results/render.py` | Use `friendly_error` for the error banner |
| `seo_analyser/forms/validators.py` | New `validate_required_fields()` (incl. conditional pairs) |
| `seo_analyser/forms/builder.py` | Demote `*_code` fields; default `language_name` to English |
| `seo_analyser/registry/catalogue.py` | Ranked, word-boundary search incl. override titles |
| `seo_analyser/labels.py` | `family_label()` plain-English family names |
| `seo_analyser/ui/home.py` | **New** landing page with task shortcuts |
| `seo_analyser/ui/sidebar.py` | No auto-selection; placeholders; family labels; new search hint |
| `seo_analyser/ui/app.py` | Route home page vs endpoint page via nav state |
| `seo_analyser/ui/endpoint_page.py` | Pending-run handling; Fetch button in history; required-field gate |
| `tests/test_tasks.py`, `tests/test_detect.py`, `tests/test_validators.py`, `tests/test_search.py`, `tests/test_labels.py`, `tests/test_store.py`, `tests/test_home.py` (new) | Tests per task |
| `docs/PROJECT-STATUS.md` | Update feature map, gotchas, backlog, session log |

---

### Task 1: Graceful pending tasks (kill the premature "Task Not Found")

**Files:**
- Modify: `seo_analyser/runner/errors.py:11-19`
- Modify: `seo_analyser/runner/tasks.py`
- Modify: `seo_analyser/persistence/store.py` (add `update_run`)
- Modify: `seo_analyser/ui/endpoint_page.py` (`_run_and_record`, `_render_history_and_presets`)
- Test: `tests/test_tasks.py`, `tests/test_store.py`

Design: when the poll window expires and the final `task_get` says "not found", do NOT show a raw API error. Raise `RunError(kind="pending")` carrying the task id; the UI records a `pending` run (with the id in the stored response, same shape `_start_prereq` uses, so the prereq id-harvester keeps working) and tells the user the truth. History rows with status `pending` get a **Fetch** button that calls `task_get` by id (free, no new task posted) and updates the same run row in place.

- [ ] **Step 1: Write failing tests for the runner logic**

Add to `tests/test_tasks.py` (it already has fakes for the SDK client; follow its existing pattern for stubbing `_api_class_for` / `_to_dict`):

```python
def test_task_not_found_detector():
    from seo_analyser.runner.tasks import task_not_found
    assert task_not_found({"tasks": [{"status_message": "Task Not Found."}]})
    assert not task_not_found({"tasks": [{"status_message": "Ok."}]})
    assert not task_not_found({})


def test_runerror_carries_task_id():
    from seo_analyser.runner.errors import RunError
    err = RunError("pending", "still processing", task_id="abc-123")
    assert err.task_id == "abc-123"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python -m pytest tests/test_tasks.py -q`
Expected: FAIL (`task_not_found` not defined; unexpected keyword `task_id`).

- [ ] **Step 3: Implement**

`seo_analyser/runner/errors.py` — add the field:

```python
@dataclass
class RunError(Exception):
    kind: str          # "auth" | "rate_limit" | "bad_request" | "server" | "network" | "empty" | "pending"
    message: str
    status_code: int | None = None
    task_id: str | None = None
```

`seo_analyser/runner/tasks.py` — add the detector and `fetch_task`, and make `run_task` raise `pending` instead of returning a not-found envelope. The poll loop currently sits at `tasks.py:50-60`; track whether the id ever appeared ready:

```python
def task_not_found(resp: dict) -> bool:
    """True when a task_get envelope reports the id as unknown (still processing)."""
    for task in resp.get("tasks") or []:
        if "not found" in (task.get("status_message") or "").lower():
            return True
    return False


def fetch_task(meta: EndpointMeta, task_id: str, creds: Credentials) -> dict:
    """Fetch an already-posted task's result by id. No new task, no new charge."""
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    _post, _ready, get_method = meta.task_methods
    if not get_method:
        raise RunError("bad_request", f"{meta.name} has no task-get method.")

    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    conf = cfg.Configuration(username=creds.login, password=creds.password)
    try:
        with prov.ApiClient(conf) as client:
            api = _api_class_for(meta.family)(client)
            return _to_dict(getattr(api, get_method)(id=task_id))
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc
```

In `run_task`, replace the tail of the polling block (after the `while` loop) with:

```python
            became_ready = task_id in ready_ids(ready) if waited else False
            result = _to_dict(getattr(api, get_method)(id=task_id))
            if task_not_found(result):
                raise RunError(
                    "pending",
                    f"The task was accepted and is still processing (id {task_id}). "
                    "It has been saved to Recent runs below; press Fetch in a minute "
                    "or two to get the result without being charged again.",
                    task_id=task_id,
                )
            return result
```

(Initialise `ready: dict = {}` before the loop so the `became_ready` line is safe; it exists only for readability and can be dropped if unused.)

`seo_analyser/persistence/store.py` — add inside `class Store` (and add `update` to the existing `sqlalchemy` import at `store.py:17-20`):

```python
    def update_run(self, run_id: int, *, cost: float, status: str,
                   response: dict | None) -> None:
        """Overwrite a run's outcome in place (used when a pending task completes)."""
        response_json = None
        if response is not None:
            blob = json.dumps(response, default=str)
            if len(blob) <= _MAX_RESPONSE_BYTES:
                response_json = blob
        with self.engine.begin() as conn:
            conn.execute(update(runs).where(runs.c.id == run_id).values(
                cost=cost, status=status, response=response_json,
            ))
```

Add a test to `tests/test_store.py` (use its existing in-memory/temp-engine fixture pattern): insert a run via `add_run(..., status="pending", response={"tasks": [{"id": "t1"}]})`, call `update_run` with `status="ok"` and a response, assert `recent_runs()[0].status == "ok"` and `load_response` returns the new body.

`seo_analyser/ui/endpoint_page.py` — in `_run_and_record` (line 37), split the error handling:

```python
    except RunError as err:
        if err.kind == "pending" and err.task_id:
            default_store().add_run(meta.name, meta.family, payload, 0.0, "pending",
                                    response={"tasks": [{"id": err.task_id}]})
            st.info(str(err))
        else:
            st.error(str(err))
        return
```

In `_render_history_and_presets` (line 275), give pending rows a Fetch button instead of View, and handle it. Add `fetch_target: tuple[int, str, str] | None = None` next to the other targets; in the row loop replace the View button block with:

```python
            if r.status == "pending":
                if cols[2].button("Fetch", key=f"fetch.{i}",
                                  help="Fetch the finished task's result (no new charge)"):
                    fetch_target = (r.id, r.family, r.endpoint)
            elif cols[2].button("View", key=f"view.{i}", disabled=not r.has_response,
                                help="Show the saved result without re-running"):
                view_target = r.id
```

And after the expanders:

```python
    if fetch_target:
        run_id, fam, ep = fetch_target
        saved = store.load_response(run_id) or {}
        task_id = extract_task_id(saved)
        meta = catalogue.find_endpoint(fam, ep)
        if not (meta and task_id):
            st.warning("No task id is stored for that run.")
        else:
            try:
                with st.spinner(f"Fetching task {task_id}..."):
                    result = fetch_task(meta, task_id, creds)
            except RunError as err:
                st.error(str(err))
                return
            if task_not_found(result):
                st.info("Still processing. Try Fetch again in a minute.")
            else:
                parsed = parse_response(result)
                store.update_run(run_id, cost=parsed.cost,
                                 status="ok" if parsed.ok else "error", response=result)
                st.subheader("Fetched result")
                render_result(result, endpoint=ep)
```

Update the imports at the top of `endpoint_page.py`: `from seo_analyser.runner.tasks import extract_task_id, fetch_task, run_task, task_not_found`.

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_tasks.py tests/test_store.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/runner/errors.py seo_analyser/runner/tasks.py \
        seo_analyser/persistence/store.py seo_analyser/ui/endpoint_page.py \
        tests/test_tasks.py tests/test_store.py
git commit -m "feat: pending tasks survive the poll window with a free Fetch from history"
```

---

### Task 2: Translate API errors into plain English

**Files:**
- Modify: `seo_analyser/results/detect.py`
- Modify: `seo_analyser/results/render.py:34-36`
- Test: `tests/test_detect.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_detect.py`:

```python
from seo_analyser.results.detect import friendly_error


def test_friendly_error_translates_invalid_field():
    msg = friendly_error("Invalid Field: 'keyword'.", 40501)
    assert "keyword" in msg
    assert "fill in" in msg.lower() or "missing" in msg.lower()
    assert "Invalid Field" in msg  # original preserved for power users


def test_friendly_error_translates_task_not_found():
    msg = friendly_error("Task Not Found.", 40401)
    assert "still be processing" in msg


def test_friendly_error_passes_through_unknown():
    assert friendly_error("You have reached your limit.", 40202) == "You have reached your limit."
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_detect.py -q` — Expected: FAIL (no `friendly_error`).

- [ ] **Step 3: Implement**

`seo_analyser/results/detect.py`:

```python
_INVALID_FIELD_RE = re.compile(r"invalid field:?\s*'?([a-z0-9_]+)'?", re.I)


def friendly_error(status_message: str, status_code: int | None = None) -> str:
    """Translate DataForSEO error phrasing into instructions a beginner can act on.

    'Invalid Field' almost always means a required field was left empty, not that
    the value was wrong; say so, but keep the original message for power users.
    """
    msg = status_message or (f"status code {status_code}" if status_code else "unknown error")
    m = _INVALID_FIELD_RE.search(msg)
    if m:
        name = m.group(1)
        return (f"'{name}' is missing or not valid. Fill in the '{name}' field "
                f"above and run again. (API said: {msg})")
    low = msg.lower()
    if "task" in low and "not found" in low:
        return ("That task id was not found. The task may still be processing "
                "(wait a minute and fetch or run again), or the id may be mistyped. "
                f"(API said: {msg})")
    return msg
```

`seo_analyser/results/render.py` — change the error banner (line 34-36):

```python
    if not parsed.ok:
        st.error("DataForSEO returned an error: "
                 + friendly_error(parsed.status_message, parsed.status_code))
```

and add `friendly_error` to the existing `detect` import at `render.py:10-13`.

- [ ] **Step 4: Run tests** — `python -m pytest tests/test_detect.py -q` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/results/detect.py seo_analyser/results/render.py tests/test_detect.py
git commit -m "feat: translate Invalid Field / Task Not Found into actionable messages"
```

---

### Task 3: Block paid calls when required fields are empty

**Files:**
- Modify: `seo_analyser/forms/validators.py`
- Modify: `seo_analyser/ui/endpoint_page.py:88-89`
- Test: `tests/test_validators.py`

The Run gate already exists (`endpoint_page.py:99-101` refuses to call when `problems` is non-empty); this task only widens what counts as a problem. Two unambiguous cases: a hard-required field left empty, and a conditional one-of-a-pair where BOTH halves are empty. Never block a conditional field on its own (see constraints in §0).

- [ ] **Step 1: Write failing tests**

Add to `tests/test_validators.py` (it already imports `FieldSpec` patterns — follow the existing style):

```python
from seo_analyser.forms.widgets import FieldSpec
from seo_analyser.forms.validators import validate_required_fields


def _spec(name, requirement="", partner=None, kind="text", default_hint=None):
    return FieldSpec(name=name, kind=kind, requirement=requirement,
                     partner=partner, default_hint=default_hint)


def test_blocks_empty_hard_required_field():
    specs = [_spec("keyword", "required")]
    assert validate_required_fields(specs, {}) != []
    assert validate_required_fields(specs, {"keyword": "indexify"}) == []


def test_skips_ids_nested_and_defaulted_fields():
    specs = [_spec("id", "required"),                       # covered by validate_required_ids
             _spec("filters", "required", kind="nested"),   # not renderable
             _spec("depth", "required", default_hint="100")]  # API has a default
    assert validate_required_fields(specs, {}) == []


def test_blocks_conditional_pair_only_when_both_empty():
    specs = [_spec("language_name", "conditional", partner="language_code"),
             _spec("language_code", "conditional", partner="language_name")]
    assert len(validate_required_fields(specs, {})) == 1  # deduplicated pair message
    assert validate_required_fields(specs, {"language_code": "en"}) == []
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_validators.py -q` — FAIL.

- [ ] **Step 3: Implement**

Append to `seo_analyser/forms/validators.py`:

```python
def validate_required_fields(specs, payload: dict) -> list[str]:
    """Flag empty required fields before a paid call is wasted on 'Invalid Field'.

    Only unambiguous cases block: hard-required fields (the introspection already
    separates 'required unless X' into requirement == "conditional"), and
    conditional pairs where neither half is filled. Id fields are handled by
    validate_required_ids; nested fields aren't renderable; fields with an API
    default are fine to omit.
    """
    warnings: list[str] = []
    filled = {k for k, v in payload.items() if v not in (None, "", [])}
    seen_pairs: set[frozenset[str]] = set()
    for spec in specs:
        if spec.name in _ID_FIELDS or spec.kind == "nested" or spec.default_hint:
            continue
        if spec.requirement == "required" and spec.name not in filled:
            warnings.append(f"'{spec.name}' is required. Fill it in before running.")
        elif spec.requirement == "conditional" and spec.partner:
            pair = frozenset((spec.name, spec.partner))
            if pair in seen_pairs or filled & pair:
                continue
            seen_pairs.add(pair)
            warnings.append(
                f"Provide either '{spec.name}' or '{spec.partner}' before running.")
    return warnings
```

Wire it in at `seo_analyser/ui/endpoint_page.py:88-89` (compute `specs = fields_for(meta.request_model)` once and reuse — it is currently called twice):

```python
    specs = fields_for(meta.request_model)
    problems = (validate_payload(payload)
                + validate_required_ids(specs, payload)
                + validate_required_fields(specs, payload))
```

(`prerequisite_for` on line 72 can reuse the same `specs` if you hoist it above.) Add the import next to the other validators import on line 10.

- [ ] **Step 4: Run tests** — `python -m pytest tests/test_validators.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/forms/validators.py seo_analyser/ui/endpoint_page.py tests/test_validators.py
git commit -m "feat: refuse to run with empty required fields or empty conditional pairs"
```

---

### Task 4: Ranked, word-boundary endpoint search

**Files:**
- Modify: `seo_analyser/registry/catalogue.py:33-43`
- Modify: `seo_analyser/ui/sidebar.py:36` (placeholder examples)
- Test: `tests/test_search.py`

Scoring per token: 3 for an exact word match, 2 for a word-prefix match, 1 for a substring match, reject the endpoint if any token matches nothing. Override titles (`overrides.yml`) join the haystack so "ai overview" finds "Google AI Mode (AI Overview)". This fixes "ai" matching the inside of "av**ai**lable" and "dom**ai**n".

- [ ] **Step 1: Write failing tests**

Add to `tests/test_search.py` (keep its existing tests; update any that asserted unranked behaviour):

```python
from seo_analyser.registry.catalogue import score_endpoint, search_endpoints
from seo_analyser.registry.introspect import EndpointMeta


def _meta(family, name):
    return EndpointMeta(name=name, family=family, request_model=None, is_task_based=False)


def test_word_match_outranks_substring():
    ai = _meta("serp", "ai_summary")
    avail = _meta("backlinks", "available_filters")
    assert score_endpoint(ai, ["ai"]) > score_endpoint(avail, ["ai"])


def test_all_tokens_must_match():
    assert score_endpoint(_meta("backlinks", "available_filters"), ["ai", "overview"]) == 0


def test_ai_overview_finds_ai_mode_first():
    top = search_endpoints("ai overview")[0]
    assert top.family in ("serp", "ai_optimization")
    assert "ai" in f"{top.name} {top.family}".replace("_", " ").split() or "ai_mode" in top.name
```

(`EndpointMeta` is the dataclass at `seo_analyser/registry/introspect.py:25` — name, family, request_model, is_task_based, plus defaulted kind/task_methods.)

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_search.py -q` — FAIL.

- [ ] **Step 3: Implement**

Replace `matches_query`/`search_endpoints` in `seo_analyser/registry/catalogue.py` with:

```python
import re

from seo_analyser.registry.overrides import override_for

_WORD_RE = re.compile(r"[a-z0-9]+")


def _haystack(e: EndpointMeta) -> tuple[list[str], str]:
    title = override_for(e.family, e.name).get("title", "")
    words = _WORD_RE.findall(f"{e.family} {e.name} {title}".lower())
    return words, " ".join(words)


def score_endpoint(e: EndpointMeta, tokens: list[str]) -> int:
    """Rank: exact word 3, word prefix 2, substring 1; 0 if any token misses."""
    words, joined = _haystack(e)
    total = 0
    for token in tokens:
        if token in words:
            total += 3
        elif any(w.startswith(token) for w in words):
            total += 2
        elif token in joined:
            total += 1
        else:
            return 0
    return total


def search_endpoints(query: str, limit: int = 50) -> list[EndpointMeta]:
    tokens = [t for t in query.lower().split() if t]
    if not tokens:
        return []
    scored = sorted(
        ((score_endpoint(e, tokens), e) for e in all_endpoints()),
        key=lambda pair: -pair[0],
    )
    return [e for s, e in scored if s > 0][:limit]
```

If anything still imports `matches_query` (check with `grep -rn matches_query`), keep it as a thin wrapper: `return score_endpoint(...) > 0` for an `EndpointMeta` built inline, or update the caller/tests instead.

In `seo_analyser/ui/sidebar.py:36`, make the placeholder examples ones that now win:

```python
        query = st.text_input("Search all endpoints",
                              placeholder="e.g. ai overview, keyword volume, backlinks")
```

- [ ] **Step 4: Run tests** — `python -m pytest tests/test_search.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/registry/catalogue.py seo_analyser/ui/sidebar.py tests/test_search.py
git commit -m "feat: rank endpoint search by word boundaries and searchable titles"
```

---

### Task 5: Landing page with task-shaped shortcuts

**Files:**
- Create: `seo_analyser/ui/home.py`
- Modify: `seo_analyser/ui/sidebar.py:50-56` (no auto-selection)
- Modify: `seo_analyser/ui/app.py:36-39` (routing)
- Test: `tests/test_home.py` (new)

Today the sidebar's selectboxes auto-pick the first family/endpoint, landing new users on a non-runnable "Available Filters" page. Change both selectboxes to `index=None` with placeholders, and when nothing is chosen render a welcome screen of 8 job-shaped shortcuts. Clicking one navigates via `st.session_state`; touching the sidebar overrides it.

- [ ] **Step 1: Write the failing test (shortcut integrity)**

Create `tests/test_home.py`:

```python
"""Every home-page shortcut must resolve to a real, runnable endpoint."""
from seo_analyser.registry import catalogue
from seo_analyser.ui.home import SHORTCUTS


def test_shortcuts_resolve_to_runnable_endpoints():
    for label, _blurb, family, endpoint in SHORTCUTS:
        meta = catalogue.find_endpoint(family, endpoint)
        assert meta is not None, f"{label}: {family}.{endpoint} not in catalogue"
        assert meta.request_model is not None, f"{label}: {family}.{endpoint} not runnable"


def test_shortcut_count_fits_grid():
    assert 6 <= len(SHORTCUTS) <= 8
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_home.py -q` — FAIL (no module).

- [ ] **Step 3: Implement the home module**

Create `seo_analyser/ui/home.py`:

```python
"""Welcome screen: maps common SEO jobs to pre-chosen endpoints.

A junior SEO should not need to know DataForSEO's API vocabulary to start;
each shortcut jumps straight to a curated endpoint (titles/descriptions for
these live in registry/overrides.yml).
"""
from __future__ import annotations

import streamlit as st

NAV_KEY = "nav_target"

# (button label, one-line blurb, family, endpoint)
SHORTCUTS = [
    ("Check Google rankings", "Top organic results for a keyword",
     "serp", "google_organic_live_advanced"),
    ("See Google's AI Overview", "Google's AI answer for a query, with sources",
     "serp", "google_ai_mode_live_advanced"),
    ("Ask ChatGPT", "Send a prompt; see the answer and its cited sources",
     "ai_optimization", "chat_gpt_llm_responses_live"),
    ("Keyword search volumes", "Monthly volume, competition and CPC",
     "keywords_data", "google_ads_search_volume_live"),
    ("Check backlinks", "Top-level backlink metrics for any domain",
     "backlinks", "backlinks_summary_live"),
    ("Keywords a site ranks for", "Positions and volumes for any domain",
     "dataforseo_labs", "google_ranked_keywords_live"),
    ("Audit a page", "Instant on-page SEO checks for a single URL",
     "on_page", "instant_pages"),
    ("Ask Claude", "Send a prompt to an Anthropic Claude model",
     "ai_optimization", "claude_llm_responses_live"),
]


def render_home() -> None:
    st.markdown("#### What do you want to do?")
    st.caption("Pick a job below, or search all 396 endpoints from the sidebar.")
    cols = st.columns(2)
    for i, (label, blurb, family, endpoint) in enumerate(SHORTCUTS):
        with cols[i % 2]:
            if st.button(label, key=f"home.{family}.{endpoint}", use_container_width=True):
                st.session_state[NAV_KEY] = (family, endpoint)
                st.rerun()
            st.caption(blurb)
```

Verify the two endpoint names you cannot see in `overrides.yml` exist before trusting them: `python -c "from seo_analyser.registry import catalogue; print(catalogue.find_endpoint('on_page','instant_pages')); print(catalogue.find_endpoint('ai_optimization','claude_llm_responses_live'))"` — if either is None, list candidates with `[e.name for e in catalogue.endpoints_for('on_page')]` and substitute the correct name. The test from Step 1 enforces this.

- [ ] **Step 4: Stop the sidebar auto-selecting**

In `seo_analyser/ui/sidebar.py`, replace lines 50-56 with:

```python
        family = st.selectbox("API family", catalogue.families(), format_func=family_label,
                              index=None, placeholder="Browse the API families...")
        if family is None:
            return creds, None, None
        endpoints = catalogue.endpoints_for(family)
        names = [e.name for e in endpoints]
        endpoint_name = st.selectbox("Endpoint", names, format_func=titleize,
                                     index=None, placeholder="Pick an endpoint...")
        st.caption(f"{len(names)} endpoints in {family_label(family)}")
    return creds, family, endpoint_name
```

(`family_label` arrives in Task 6; if you do this task first, keep `titleize` and swap later.)

- [ ] **Step 5: Route in the app shell**

In `seo_analyser/ui/app.py`, replace lines 36-39 with:

```python
    if family and endpoint_name:
        st.session_state.pop(NAV_KEY, None)   # sidebar choice overrides a shortcut
        render_endpoint_page(creds, family, endpoint_name)
    elif st.session_state.get(NAV_KEY):
        nav_family, nav_endpoint = st.session_state[NAV_KEY]
        render_endpoint_page(creds, nav_family, nav_endpoint)
    else:
        render_home()
```

with the import `from seo_analyser.ui.home import NAV_KEY, render_home`.

- [ ] **Step 6: Run tests and check in the browser**

Run: `python -m pytest tests/test_home.py -q` — PASS.
Run the app; with credentials entered you should land on the shortcut grid, a shortcut click should open its endpoint page, and picking a family+endpoint in the sidebar should override it. With no credentials the existing sidebar prompt still shows first.

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/ui/home.py seo_analyser/ui/sidebar.py seo_analyser/ui/app.py tests/test_home.py
git commit -m "feat: task-shaped landing page; sidebar no longer auto-selects a dead end"
```

---

### Task 6: Plain-English family names

**Files:**
- Modify: `seo_analyser/labels.py`
- Modify: `seo_analyser/ui/sidebar.py` (format_func), `seo_analyser/ui/endpoint_page.py:60` (caption)
- Test: `tests/test_labels.py`

- [ ] **Step 1: List the real families**

Run: `python -c "from seo_analyser.registry import catalogue; print(catalogue.families())"`
Use the output to make the map below cover every family (the names below are the expected 13; correct any that differ).

- [ ] **Step 2: Write the failing test**

Add to `tests/test_labels.py`:

```python
from seo_analyser.labels import family_label
from seo_analyser.registry import catalogue


def test_every_family_has_a_plain_english_label():
    for fam in catalogue.families():
        label = family_label(fam)
        assert label and "_" not in label


def test_family_label_falls_back_to_titleize():
    assert family_label("made_up_family") == "Made Up Family"
```

- [ ] **Step 3: Implement** (in `seo_analyser/labels.py`)

```python
# Junior-SEO-friendly names for API families; fall back to titleize for new ones.
_FAMILY_LABELS = {
    "serp": "Rankings (SERP)",
    "keywords_data": "Keyword Volumes",
    "dataforseo_labs": "Keyword & Competitor Research",
    "backlinks": "Backlinks",
    "on_page": "Site Audits (On-Page)",
    "ai_optimization": "AI Visibility (LLMs)",
    "content_analysis": "Brand Mentions",
    "content_generation": "Content Generation",
    "domain_analytics": "Domain Tech & Whois",
    "business_data": "Business Listings & Reviews",
    "merchant": "Amazon & Shopping",
    "app_data": "App Stores",
    "appendix": "Account & Admin",
}


def family_label(name: str) -> str:
    """Plain-English family name for menus, e.g. 'serp' -> 'Rankings (SERP)'."""
    return _FAMILY_LABELS.get(name) or titleize(name)
```

Use it: sidebar `format_func=family_label` (both the family selectbox and the search-hit labels at `sidebar.py:42-45`), and the endpoint page caption at `endpoint_page.py:60`:

```python
    st.caption(f"{family_label(family)}  ·  `{endpoint_name}`")
```

- [ ] **Step 4: Run tests** — `python -m pytest tests/test_labels.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/labels.py seo_analyser/ui/sidebar.py seo_analyser/ui/endpoint_page.py tests/test_labels.py
git commit -m "feat: plain-English family names in menus"
```

---

### Task 7: Form polish — codes under Advanced, language defaults to English

**Files:**
- Modify: `seo_analyser/forms/builder.py`
- Test: `tests/test_builder.py`

Two changes: (1) when both `location_name` and `location_code` (or the language pair) exist on a form, the `*_code` twin moves under "Advanced options" — names are enough for beginners; (2) the `language_name` quick-pick dropdown defaults to "English" instead of blank, which also satisfies the Task 3 pair-check out of the box.

- [ ] **Step 1: Write the failing test**

`render_form` is Streamlit-bound, so test the partition logic. Extract it to a pure function first (see Step 3) and test that:

```python
from seo_analyser.forms.builder import split_common_advanced
from seo_analyser.forms.widgets import FieldSpec


def _spec(name, requirement=""):
    return FieldSpec(name=name, kind="text", requirement=requirement)


def test_code_twin_demoted_when_name_present():
    specs = [_spec("language_name", "conditional"), _spec("language_code", "conditional")]
    common, advanced = split_common_advanced(specs)
    assert [s.name for s in common] == ["language_name"]
    assert [s.name for s in advanced] == ["language_code"]


def test_code_stays_upfront_without_name_twin():
    specs = [_spec("language_code", "required")]
    common, _advanced = split_common_advanced(specs)
    assert [s.name for s in common] == ["language_code"]
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_builder.py -q` — FAIL.

- [ ] **Step 3: Implement**

In `seo_analyser/forms/builder.py`, replace the inline partition inside `render_form` (lines 37-44) with a testable function:

```python
def split_common_advanced(specs: list[FieldSpec]) -> tuple[list[FieldSpec], list[FieldSpec]]:
    """Partition fields into up-front vs Advanced.

    Required/conditional and well-known fields go up front, except a *_code field
    whose *_name twin is on the same form: names are friendlier, so the code twin
    moves to Advanced even though the API marks it conditional.
    """
    names = {s.name for s in specs}

    def is_upfront(spec: FieldSpec) -> bool:
        if spec.name in ("location_code", "language_code") \
                and spec.name.replace("_code", "_name") in names:
            return False
        return spec.name in _COMMON_FIELDS or spec.requirement in ("required", "conditional")

    common = [s for s in specs if is_upfront(s)]
    advanced = [s for s in specs if not is_upfront(s)]
    if not common:  # nothing well-known — don't bury the whole form
        return advanced, []
    return common, advanced
```

and call it from `render_form`: `common, advanced = split_common_advanced(specs)`.

For the English default, in `_render_combobox` (line 112) give the selectbox a default index:

```python
_DEFAULT_CHOICES = {"language_name": "English"}


def _render_combobox(spec: FieldSpec, label: str, help_text, key: str,
                     presets: list[tuple[str, Any]]) -> Any:
    """Dropdown of common presets plus an 'Other' option for free text."""
    by_label = {lbl: val for lbl, val in presets}
    options = [""] + list(by_label) + [_OTHER]
    default = _DEFAULT_CHOICES.get(spec.name)
    index = options.index(default) if default in options else 0
    choice = st.selectbox(label, options, index=index, help=help_text, key=key)
    ...  # rest unchanged
```

- [ ] **Step 4: Run tests** — `python -m pytest tests/test_builder.py -q` — PASS.

- [ ] **Step 5: Commit**

```bash
git add seo_analyser/forms/builder.py tests/test_builder.py
git commit -m "feat: demote code twins to Advanced; default language to English"
```

---

### Task 8: Full verification, docs, deploy (with Jon's go-ahead)

**Files:**
- Modify: `docs/PROJECT-STATUS.md` (§5 feature map, §7 gotchas, §8 backlog, §10 session log)

- [ ] **Step 1: Full test suite**

Run: `python -m pytest -q` — Expected: all passing (88 at handover plus the new ones; zero failures). Fix anything red before proceeding.

- [ ] **Step 2: Manual browser pass (local, cheap)**

Run `streamlit run app.py --server.port 8501` and walk the junior-SEO path:
1. Cold landing with creds: shortcut grid appears (no "isn't runnable yet" page).
2. Search "ai overview": an AI Overview endpoint is the top hit.
3. "Check Google rankings" shortcut → click Run with the form EMPTY → blocked with a clear message, **no API call made** (balance unchanged).
4. Fill keyword "indexify"; language already defaults to English; Run → OK result (~$0.002).
5. Sidebar family list shows plain-English names; location/language *codes* are under Advanced.
6. Ask ChatGPT shortcut → submit a prompt; if it outruns the poll window, confirm the pending message appears, the run shows in Recent runs with a Fetch button, and Fetch retrieves the result a minute later. (This is the exact bug Jon hit; spend the ~$0.01 to prove it fixed.)

- [ ] **Step 3: Update the status doc**

In `docs/PROJECT-STATUS.md`: add the new features to §5; revise the §7 gotcha that said "we DON'T hard-block on generic required" (we now block hard-required and empty pairs — conditional singles still never block); cross "tighten fuzzy search" off §8; add a §10 session-log entry describing this work. Commit:

```bash
git add docs/PROJECT-STATUS.md
git commit -m "docs: record junior-SEO UX pass in the working doc"
```

- [ ] **Step 4: Get the go-ahead, deploy, verify live**

**Pushing to `main` deploys to production automatically.** Ask Jon before pushing. After the Railway build goes ACTIVE, repeat the quick checks from Step 2 (items 1-4) against https://seo-data-tool.up.railway.app and report what you verified, including actual spend.

---

## Self-review checklist (run before handing back)

- Every audit finding in §0 maps to a task: premature Task Not Found → Task 1; Invalid Field translation → Task 2; money-burning empty runs → Task 3; broken search and placeholder → Task 4; dead-end landing → Task 5; API vocabulary → Tasks 6-7.
- No silent behaviour changes beyond the listed ones; conditional single fields still never block (constraint in §0).
- `docs/PROJECT-STATUS.md` updated and the live site verified, not just localhost.
