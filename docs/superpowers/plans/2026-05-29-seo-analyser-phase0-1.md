# SEO Analyzer Tool — Phase 0 + Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the `dataforseo-client` SDK introspects as designed (Phase 0), then build a generic Streamlit runner that auto-generates a form for any endpoint and executes a live call (Phase 1).

**Architecture:** Walk `dataforseo_client.api.*` to build a catalogue of endpoints and their Pydantic request models. A form builder turns a request model's fields into widget specs; the UI renders them, collects input, and the live runner calls the SDK method. UI-free layers (registry, forms, runner) are unit-tested; Streamlit rendering is smoke-tested manually.

**Tech Stack:** Python 3.14, Streamlit 1.32, `dataforseo-client` SDK, Pydantic v2, pytest.

**Branch:** all work on `rebuild/seo-analyser`.

**Spec:** `docs/superpowers/specs/2026-05-29-seo-analyser-design.md` (Phases 0–1).

---

## File Structure

| File | Responsibility |
|------|----------------|
| `requirements.txt` (modify) | add `dataforseo-client`, `pydantic>=2`, `pytest` |
| `seo_analyser/__init__.py` (create) | package marker |
| `seo_analyser/registry/__init__.py` (create) | package marker |
| `seo_analyser/registry/introspect.py` (create) | walk SDK, build catalogue of `EndpointMeta` |
| `seo_analyser/registry/catalogue.py` (create) | cached singleton catalogue + JSON dump |
| `seo_analyser/forms/__init__.py` (create) | package marker |
| `seo_analyser/forms/widgets.py` (create) | `FieldSpec` + type→spec mapping + enum/range parsing |
| `seo_analyser/forms/builder.py` (create) | model→`list[FieldSpec]`; render specs; collect payload |
| `seo_analyser/runner/__init__.py` (create) | package marker |
| `seo_analyser/runner/errors.py` (create) | normalise SDK exceptions to `RunError` |
| `seo_analyser/runner/live.py` (create) | execute a live endpoint via the SDK |
| `seo_analyser/auth.py` (create) | credentials from sidebar / `.env.local` |
| `seo_analyser/ui/__init__.py` (create) | package marker |
| `seo_analyser/ui/sidebar.py` (create) | creds + family/endpoint picker |
| `seo_analyser/ui/endpoint_page.py` (create) | form + run button + JSON result |
| `seo_analyser/ui/app.py` (create) | `main()` wiring sidebar + page |
| `app.py` (modify at end) | thin entrypoint → `seo_analyser.ui.app:main` (Phase 5 swaps fully; Phase 1 leaves old app intact, adds new entry via `app_v2.py`) |
| `tests/__init__.py` (create) | package marker |
| `tests/test_introspect.py` (create) | catalogue build assertions |
| `tests/test_widgets.py` (create) | field-spec + enum/range parsing assertions |
| `tests/test_errors.py` (create) | exception normalisation assertions |

**Note on `http_path`:** the spec catalogue mentions `http_path`. The SDK's generated methods own the path internally, so the runner never needs it. We key endpoints by `(family, method_name)` and drop `http_path` from Phase 0 to avoid brittle docstring parsing. Revisit only if a later phase needs it for display.

**Note on the new entrypoint:** to keep `main` deployable during the rebuild (decision H), Phase 1 adds `app_v2.py` as the new entrypoint and leaves the old `app.py` untouched. Phase 5 archives `app.py` and renames `app_v2.py` → `app.py`.

---

## Task 1: Branch + environment

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Create the feature branch**

Run:
```bash
git checkout -b rebuild/seo-analyser
```
Expected: `Switched to a new branch 'rebuild/seo-analyser'`

- [ ] **Step 2: Create a virtualenv and activate it**

Run:
```bash
python3 -m venv .venv && source .venv/bin/activate && python --version
```
Expected: prints `Python 3.14.x`

- [ ] **Step 3: Update requirements.txt**

Replace the contents of `requirements.txt` with:
```
streamlit==1.32.0
pandas==2.2.0
plotly==5.19.0
requests==2.31.0
dataforseo-client>=1.0.0
pydantic>=2.0
pytest>=8.0
```

- [ ] **Step 4: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```
Expected: installs without error; `pip show dataforseo-client` prints a version.

- [ ] **Step 5: Add .venv and __pycache__ to .gitignore**

Append to `.gitignore` (only if not already present):
```
.venv/
__pycache__/
*.pyc
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "chore: add SDK + pytest deps, ignore venv/pycache"
```

---

## Task 2: SDK introspection (Phase 0 — the gate)

**Files:**
- Create: `seo_analyser/__init__.py`
- Create: `seo_analyser/registry/__init__.py`
- Create: `seo_analyser/registry/introspect.py`
- Test: `tests/test_introspect.py`, `tests/__init__.py`

- [ ] **Step 1: Create package markers**

Create `seo_analyser/__init__.py` (empty), `seo_analyser/registry/__init__.py` (empty), `tests/__init__.py` (empty).

- [ ] **Step 2: Write the failing test**

Create `tests/test_introspect.py`:
```python
from seo_analyser.registry.introspect import build_catalogue, EndpointMeta

CATALOGUE = build_catalogue()

EXPECTED_FAMILIES = {
    "serp", "keywords_data", "business_data", "dataforseo_labs",
    "ai_optimization", "app_data", "merchant", "on_page",
    "backlinks", "domain_analytics", "content_analysis",
    "content_generation", "appendix",
}


def test_all_families_present():
    assert set(CATALOGUE.keys()) == EXPECTED_FAMILIES


def test_serp_is_largest_family():
    counts = {fam: len(eps) for fam, eps in CATALOGUE.items()}
    assert max(counts, key=counts.get) == "serp"
    # 181 canonical SERP endpoints per endpoint-inventory.md; allow drift across SDK versions
    assert counts["serp"] > 100


def test_endpoint_meta_shape():
    serp = CATALOGUE["serp"]
    organic = next(e for e in serp if e.name == "google_organic_live_advanced")
    assert isinstance(organic, EndpointMeta)
    assert organic.request_model is not None
    # the request model must expose Pydantic fields
    assert hasattr(organic.request_model, "model_fields")
    assert "keyword" in organic.request_model.model_fields


def test_variants_are_filtered_out():
    for eps in CATALOGUE.values():
        for e in eps:
            assert not e.name.endswith("_with_http_info")
            assert not e.name.endswith("_without_preload_content")


def test_task_based_detection():
    serp = CATALOGUE["serp"]
    assert any(e.is_task_based for e in serp)
```

- [ ] **Step 3: Run the test to verify it fails**

Run:
```bash
pytest tests/test_introspect.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'seo_analyser.registry.introspect'`

- [ ] **Step 4: Write the implementation**

Create `seo_analyser/registry/introspect.py`:
```python
"""Walk the dataforseo-client SDK and build a catalogue of endpoints.

The SDK exposes 13 API-family modules under dataforseo_client.api.*, each with
one Api class. Every endpoint is a public method whose request payload is a
Pydantic v2 BaseModel. The generator emits three variants per endpoint; we keep
only the canonical one.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass

import dataforseo_client.api as api_pkg
from pydantic import BaseModel

_VARIANT_SUFFIXES = ("_with_http_info", "_without_preload_content")


@dataclass(frozen=True)
class EndpointMeta:
    name: str            # SDK method name, e.g. "google_organic_live_advanced"
    family: str          # e.g. "serp"
    request_model: type | None   # Pydantic request model class, or None for GET-only
    is_task_based: bool  # True when this is a *_task_post method


def _api_class(module) -> type:
    """Return the single class ending in 'Api' defined in this module."""
    return next(
        cls for name, cls in inspect.getmembers(module, inspect.isclass)
        if name.endswith("Api") and cls.__module__ == module.__name__
    )


def _request_model(method) -> type | None:
    """Find the parameter annotated as a Pydantic BaseModel subclass."""
    try:
        sig = inspect.signature(method)
    except (ValueError, TypeError):
        return None
    for param in sig.parameters.values():
        ann = param.annotation
        if inspect.isclass(ann) and issubclass(ann, BaseModel):
            return ann
        # SDK often types the body as List[Model]; unwrap one level
        args = getattr(ann, "__args__", ())
        for a in args:
            if inspect.isclass(a) and issubclass(a, BaseModel):
                return a
    return None


def build_catalogue() -> dict[str, list[EndpointMeta]]:
    catalogue: dict[str, list[EndpointMeta]] = {}
    for _, mod_name, _ in pkgutil.iter_modules(api_pkg.__path__):
        module = importlib.import_module(f"dataforseo_client.api.{mod_name}")
        api_class = _api_class(module)
        family = mod_name[:-4] if mod_name.endswith("_api") else mod_name
        endpoints: list[EndpointMeta] = []
        for method_name, method in inspect.getmembers(api_class, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            if method_name.endswith(_VARIANT_SUFFIXES):
                continue
            endpoints.append(
                EndpointMeta(
                    name=method_name,
                    family=family,
                    request_model=_request_model(method),
                    is_task_based=method_name.endswith("_task_post"),
                )
            )
        catalogue[family] = endpoints
    return catalogue


if __name__ == "__main__":
    cat = build_catalogue()
    total = sum(len(v) for v in cat.values())
    for fam in sorted(cat, key=lambda f: -len(cat[f])):
        print(f"{fam:<22} {len(cat[fam])}")
    print(f"{'TOTAL':<22} {total}")
```

- [ ] **Step 5: Run the test to verify it passes**

Run:
```bash
pytest tests/test_introspect.py -v
```
Expected: all 5 tests PASS. If `test_all_families_present` fails because the SDK uses different module names, print `python -m seo_analyser.registry.introspect` and reconcile `EXPECTED_FAMILIES` to the real names — **this is the Phase 0 gate; investigate any divergence before continuing.**

- [ ] **Step 6: Eyeball the catalogue manually**

Run:
```bash
python -m seo_analyser.registry.introspect
```
Expected: a family/count table with `serp` largest and a `TOTAL` near 565 (canonical endpoints; exact number may drift by SDK version). **Confirm the order of magnitude is right before proceeding.**

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/__init__.py seo_analyser/registry tests/__init__.py tests/test_introspect.py
git commit -m "feat: SDK introspection catalogue (Phase 0 gate)"
```

---

## Task 3: Cached catalogue accessor

**Files:**
- Create: `seo_analyser/registry/catalogue.py`

This wraps `build_catalogue()` so the app builds it once. No new test — it is a thin cache over the tested `build_catalogue`.

- [ ] **Step 1: Write the implementation**

Create `seo_analyser/registry/catalogue.py`:
```python
"""Process-wide cached access to the endpoint catalogue."""
from __future__ import annotations

from functools import lru_cache

from seo_analyser.registry.introspect import EndpointMeta, build_catalogue


@lru_cache(maxsize=1)
def get_catalogue() -> dict[str, list[EndpointMeta]]:
    return build_catalogue()


def families() -> list[str]:
    return sorted(get_catalogue().keys())


def endpoints_for(family: str) -> list[EndpointMeta]:
    return get_catalogue().get(family, [])


def find_endpoint(family: str, name: str) -> EndpointMeta | None:
    return next((e for e in endpoints_for(family) if e.name == name), None)
```

- [ ] **Step 2: Sanity-check import**

Run:
```bash
python -c "from seo_analyser.registry.catalogue import families; print(families())"
```
Expected: prints the sorted list of 13 family names.

- [ ] **Step 3: Commit**

```bash
git add seo_analyser/registry/catalogue.py
git commit -m "feat: cached catalogue accessor"
```

---

## Task 4: Field specs + enum/range parsing

**Files:**
- Create: `seo_analyser/forms/__init__.py`
- Create: `seo_analyser/forms/widgets.py`
- Test: `tests/test_widgets.py`

- [ ] **Step 1: Create the package marker**

Create `seo_analyser/forms/__init__.py` (empty).

- [ ] **Step 2: Write the failing test**

Create `tests/test_widgets.py`:
```python
from typing import List, Optional

from pydantic import BaseModel, Field, StrictBool, StrictInt, StrictStr

from seo_analyser.forms.widgets import FieldSpec, extract_choices, extract_range, fields_for


class _Sample(BaseModel):
    keyword: Optional[StrictStr] = Field(default=None, description="keyword required field")
    depth: Optional[StrictInt] = Field(default=None, description="parsing depth, max value: 200")
    device: Optional[StrictStr] = Field(default=None, description="possible values: desktop, mobile")
    group: Optional[StrictBool] = Field(default=True, description="default value: true")
    keywords: Optional[List[StrictStr]] = Field(default=None, description="list of keywords")


def test_extract_choices():
    assert extract_choices("possible values: desktop, mobile") == ["desktop", "mobile"]
    assert extract_choices("no enum here") == []


def test_extract_range():
    assert extract_range("parsing depth, max value: 200") == (None, 200)
    assert extract_range("range: 240-9999") == (240, 9999)
    assert extract_range("possible values from 1 to 4") == (1, 4)
    assert extract_range("no range") == (None, None)


def test_fields_for_kinds():
    specs = {f.name: f for f in fields_for(_Sample)}
    assert specs["keyword"].kind == "text"
    assert specs["depth"].kind == "int"
    assert specs["depth"].max == 200
    assert specs["device"].kind == "select"
    assert specs["device"].choices == ["desktop", "mobile"]
    assert specs["group"].kind == "bool"
    assert specs["group"].default is True
    assert specs["keywords"].kind == "list"


def test_fieldspec_carries_description():
    specs = {f.name: f for f in fields_for(_Sample)}
    assert "required" in specs["keyword"].description
```

- [ ] **Step 3: Run the test to verify it fails**

Run:
```bash
pytest tests/test_widgets.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'seo_analyser.forms.widgets'`

- [ ] **Step 4: Write the implementation**

Create `seo_analyser/forms/widgets.py`:
```python
"""Map Pydantic request-model fields to UI-agnostic widget specs.

A FieldSpec is what the UI needs to render a widget; it carries no Streamlit
dependency so it can be unit-tested.
"""
from __future__ import annotations

import re
import typing
from dataclasses import dataclass, field
from typing import Any

_CHOICE_RE = re.compile(r"possible values:?\s*([a-z0-9_]+(?:\s*,\s*[a-z0-9_]+)+)", re.I)
_MAX_RE = re.compile(r"max(?:imum)? value:?\s*(\d+)", re.I)
_RANGE_RE = re.compile(r"range:?\s*(\d+)\s*-\s*(\d+)", re.I)
_FROM_TO_RE = re.compile(r"from\s+(\d+)\s+to\s+(\d+)", re.I)


@dataclass
class FieldSpec:
    name: str
    kind: str            # "text" | "int" | "float" | "bool" | "select" | "list" | "nested"
    description: str = ""
    default: Any = None
    choices: list[str] = field(default_factory=list)
    min: int | None = None
    max: int | None = None


def extract_choices(description: str) -> list[str]:
    m = _CHOICE_RE.search(description or "")
    if not m:
        return []
    return [c.strip() for c in m.group(1).split(",") if c.strip()]


def extract_range(description: str) -> tuple[int | None, int | None]:
    text = description or ""
    m = _RANGE_RE.search(text) or _FROM_TO_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _MAX_RE.search(text)
    if m:
        return None, int(m.group(1))
    return None, None


def _base_type(annotation: Any) -> Any:
    """Strip Optional/Union, return the meaningful inner type."""
    args = typing.get_args(annotation)
    if not args:
        return annotation
    non_none = [a for a in args if a is not type(None)]
    return non_none[0] if non_none else annotation


def _kind_for(annotation: Any) -> tuple[str, Any]:
    """Return (kind, inner_for_list)."""
    inner = _base_type(annotation)
    origin = typing.get_origin(inner)
    if origin in (list, typing.List):
        return "list", inner
    name = getattr(inner, "__name__", str(inner)).lower()
    if "bool" in name:
        return "bool", inner
    if "int" in name:
        return "int", inner
    if "float" in name:
        return "float", inner
    return "text", inner


def fields_for(model: type) -> list[FieldSpec]:
    specs: list[FieldSpec] = []
    for fname, finfo in model.model_fields.items():
        desc = finfo.description or ""
        default = finfo.default
        kind, _inner = _kind_for(finfo.annotation)
        choices = extract_choices(desc)
        lo, hi = extract_range(desc)
        if kind == "text" and choices:
            kind = "select"
        specs.append(
            FieldSpec(
                name=fname, kind=kind, description=desc,
                default=default, choices=choices, min=lo, max=hi,
            )
        )
    return specs
```

- [ ] **Step 5: Run the test to verify it passes**

Run:
```bash
pytest tests/test_widgets.py -v
```
Expected: all 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add seo_analyser/forms tests/test_widgets.py
git commit -m "feat: field specs with enum/range extraction"
```

---

## Task 5: Error normalisation

**Files:**
- Create: `seo_analyser/runner/__init__.py`
- Create: `seo_analyser/runner/errors.py`
- Test: `tests/test_errors.py`

- [ ] **Step 1: Create the package marker**

Create `seo_analyser/runner/__init__.py` (empty).

- [ ] **Step 2: Write the failing test**

Create `tests/test_errors.py`:
```python
from seo_analyser.runner.errors import RunError, normalise


class _FakeApiException(Exception):
    def __init__(self, status, body=""):
        super().__init__(body)
        self.status = status
        self.body = body


def test_auth_error():
    err = normalise(_FakeApiException(401, "unauthorized"))
    assert isinstance(err, RunError)
    assert err.kind == "auth"
    assert err.status_code == 401


def test_rate_limit():
    assert normalise(_FakeApiException(429)).kind == "rate_limit"


def test_bad_request():
    assert normalise(_FakeApiException(404)).kind == "bad_request"


def test_server_error():
    assert normalise(_FakeApiException(500)).kind == "server"


def test_network_error():
    assert normalise(ConnectionError("boom")).kind == "network"
```

- [ ] **Step 3: Run the test to verify it fails**

Run:
```bash
pytest tests/test_errors.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'seo_analyser.runner.errors'`

- [ ] **Step 4: Write the implementation**

Create `seo_analyser/runner/errors.py`:
```python
"""Normalise SDK / network exceptions into a single app-level error type.

No Streamlit imports here — the UI layer catches RunError and decides how to
display it. This keeps the runner testable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunError(Exception):
    kind: str          # "auth" | "rate_limit" | "bad_request" | "server" | "network" | "empty"
    message: str
    status_code: int | None = None

    def __str__(self) -> str:
        return f"[{self.kind}] {self.message}"


def normalise(exc: Exception) -> RunError:
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    body = getattr(exc, "body", None) or str(exc)
    if isinstance(status, int):
        if status == 401 or status == 403:
            return RunError("auth", "Authentication failed — check your DataForSEO login/password.", status)
        if status == 429:
            return RunError("rate_limit", "Rate limited by DataForSEO — slow down and retry.", status)
        if 400 <= status < 500:
            return RunError("bad_request", f"Bad request: {body}", status)
        if status >= 500:
            return RunError("server", "DataForSEO server error — try again shortly.", status)
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return RunError("network", f"Network error: {exc}")
    return RunError("network", f"Unexpected error: {exc}")
```

- [ ] **Step 5: Run the test to verify it passes**

Run:
```bash
pytest tests/test_errors.py -v
```
Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add seo_analyser/runner tests/test_errors.py
git commit -m "feat: normalise SDK errors to RunError"
```

---

## Task 6: Auth + live runner

**Files:**
- Create: `seo_analyser/auth.py`
- Create: `seo_analyser/runner/live.py`

These two are I/O layers requiring real credentials, so they are smoke-tested via the UI (Task 8 acceptance) rather than unit-tested. Keep them small.

- [ ] **Step 1: Write auth.py**

Create `seo_analyser/auth.py`:
```python
"""Credential handling. Reads .env.local for local dev; the UI may override."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env.local"


@dataclass
class Credentials:
    login: str
    password: str

    @property
    def is_complete(self) -> bool:
        return bool(self.login and self.password)


def from_env() -> Credentials:
    """Best-effort read of DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD from env or .env.local."""
    login = os.environ.get("DATAFORSEO_LOGIN", "")
    password = os.environ.get("DATAFORSEO_PASSWORD", "")
    if (not login or not password) and _ENV_FILE.exists():
        for raw in _ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key == "DATAFORSEO_LOGIN" and not login:
                login = val
            elif key == "DATAFORSEO_PASSWORD" and not password:
                password = val
    return Credentials(login=login, password=password)
```

- [ ] **Step 2: Write live.py**

Create `seo_analyser/runner/live.py`:
```python
"""Execute a live endpoint through the SDK.

Builds a Configuration from credentials, instantiates the right Api class,
calls the method with a list-wrapped request model, and returns the parsed
response as a plain dict. Raises RunError on failure.
"""
from __future__ import annotations

import importlib
import inspect

from seo_analyser.auth import Credentials
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.runner.errors import RunError, normalise


def _api_class_for(family: str):
    module = importlib.import_module(f"dataforseo_client.api.{family}_api")
    return next(
        cls for name, cls in inspect.getmembers(module, inspect.isclass)
        if name.endswith("Api") and cls.__module__ == module.__name__
    )


def run_live(meta: EndpointMeta, payload: dict, creds: Credentials) -> dict:
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    if meta.request_model is None:
        raise RunError("bad_request", f"{meta.name} has no request model — not runnable yet.")

    from dataforseo_client import api_client as dfs_api_provider
    from dataforseo_client import configuration as dfs_config

    config = dfs_config.Configuration(username=creds.login, password=creds.password)
    try:
        request_obj = meta.request_model(**payload)
        with dfs_api_provider.ApiClient(config) as client:
            api = _api_class_for(meta.family)(client)
            method = getattr(api, meta.name)
            response = method([request_obj])
        return _to_dict(response)
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc


def _to_dict(response) -> dict:
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if isinstance(response, dict):
        return response
    return {"result": str(response)}
```

- [ ] **Step 3: Sanity-check imports**

Run:
```bash
python -c "from seo_analyser.runner.live import run_live; from seo_analyser.auth import from_env; print('ok')"
```
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add seo_analyser/auth.py seo_analyser/runner/live.py
git commit -m "feat: credentials + live endpoint runner"
```

---

## Task 7: Form builder (rendering)

**Files:**
- Create: `seo_analyser/forms/builder.py`

Renders `FieldSpec`s to Streamlit widgets and collects a payload dict. Streamlit rendering is smoke-tested via the UI, not unit tests.

- [ ] **Step 1: Write builder.py**

Create `seo_analyser/forms/builder.py`:
```python
"""Render FieldSpecs as Streamlit widgets and collect a payload dict."""
from __future__ import annotations

from typing import Any

import streamlit as st

from seo_analyser.forms.widgets import FieldSpec, fields_for


def render_form(model: type, key_prefix: str) -> dict[str, Any]:
    """Render one widget per field. Returns {field_name: value} with empties dropped."""
    payload: dict[str, Any] = {}
    for spec in fields_for(model):
        value = _render_field(spec, key=f"{key_prefix}.{spec.name}")
        if value not in (None, "", []):
            payload[spec.name] = value
    return payload


def _render_field(spec: FieldSpec, key: str) -> Any:
    help_text = spec.description or None
    label = spec.name
    if spec.kind == "bool":
        return st.checkbox(label, value=bool(spec.default), help=help_text, key=key)
    if spec.kind == "select":
        options = [""] + spec.choices
        return st.selectbox(label, options, help=help_text, key=key) or None
    if spec.kind == "int":
        return _number(label, spec, help_text, key, is_float=False)
    if spec.kind == "float":
        return _number(label, spec, help_text, key, is_float=True)
    if spec.kind == "list":
        raw = st.text_area(f"{label} (one per line)", help=help_text, key=key)
        return [line.strip() for line in raw.splitlines() if line.strip()]
    if spec.kind == "nested":
        st.caption(f"{label}: advanced nested field — not editable in this view yet.")
        return None
    return st.text_input(label, help=help_text, key=key) or None


def _number(label, spec: FieldSpec, help_text, key, is_float: bool):
    kwargs: dict[str, Any] = {"help": help_text, "key": key, "value": None}
    if spec.min is not None:
        kwargs["min_value"] = float(spec.min) if is_float else int(spec.min)
    if spec.max is not None:
        kwargs["max_value"] = float(spec.max) if is_float else int(spec.max)
    if not is_float:
        kwargs["step"] = 1
    return st.number_input(label, **kwargs)
```

- [ ] **Step 2: Sanity-check import**

Run:
```bash
python -c "import seo_analyser.forms.builder; print('ok')"
```
Expected: prints `ok` (Streamlit imports cleanly outside a run context).

- [ ] **Step 3: Commit**

```bash
git add seo_analyser/forms/builder.py
git commit -m "feat: render field specs as Streamlit widgets"
```

---

## Task 8: UI wiring + new entrypoint

**Files:**
- Create: `seo_analyser/ui/__init__.py`
- Create: `seo_analyser/ui/sidebar.py`
- Create: `seo_analyser/ui/endpoint_page.py`
- Create: `seo_analyser/ui/app.py`
- Create: `app_v2.py`

- [ ] **Step 1: Create the package marker**

Create `seo_analyser/ui/__init__.py` (empty).

- [ ] **Step 2: Write sidebar.py**

Create `seo_analyser/ui/sidebar.py`:
```python
"""Sidebar: credentials + family/endpoint picker."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials, from_env
from seo_analyser.registry import catalogue


def render_sidebar() -> tuple[Credentials, str | None, str | None]:
    env = from_env()
    with st.sidebar:
        st.header("DataForSEO credentials")
        login = st.text_input("Login", value=env.login)
        password = st.text_input("Password", value=env.password, type="password")
        creds = Credentials(login=login, password=password)

        st.header("Endpoint")
        family = st.selectbox("API family", catalogue.families())
        endpoints = catalogue.endpoints_for(family)
        names = [e.name for e in endpoints]
        endpoint_name = st.selectbox("Endpoint", names) if names else None
    return creds, family, endpoint_name
```

- [ ] **Step 3: Write endpoint_page.py**

Create `seo_analyser/ui/endpoint_page.py`:
```python
"""Endpoint page: auto-form + Run + raw JSON result."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials
from seo_analyser.forms.builder import render_form
from seo_analyser.registry import catalogue
from seo_analyser.runner.errors import RunError
from seo_analyser.runner.live import run_live


def render_endpoint_page(creds: Credentials, family: str, endpoint_name: str) -> None:
    meta = catalogue.find_endpoint(family, endpoint_name)
    if meta is None:
        st.warning("Select an endpoint from the sidebar.")
        return

    st.subheader(f"{family} · {endpoint_name}")
    if meta.is_task_based:
        st.info("This is a task-based endpoint. Task polling lands in Phase 2 — running it live may not return results yet.")
    if meta.request_model is None:
        st.warning("This endpoint takes no request body and isn't runnable in Phase 1.")
        return

    payload = render_form(meta.request_model, key_prefix=f"{family}.{endpoint_name}")

    if st.button("Run", type="primary"):
        with st.spinner("Calling DataForSEO..."):
            try:
                result = run_live(meta, payload, creds)
            except RunError as err:
                st.error(str(err))
                return
        st.success("Done.")
        st.json(result)
```

- [ ] **Step 4: Write app.py (the new main)**

Create `seo_analyser/ui/app.py`:
```python
"""SEO Analyzer Tool — auto-generated DataForSEO gateway."""
from __future__ import annotations

import streamlit as st

from seo_analyser.ui.endpoint_page import render_endpoint_page
from seo_analyser.ui.sidebar import render_sidebar


def main() -> None:
    st.set_page_config(page_title="SEO Analyzer Tool", layout="wide")
    st.title("SEO Analyzer Tool")
    creds, family, endpoint_name = render_sidebar()
    if family and endpoint_name:
        render_endpoint_page(creds, family, endpoint_name)
    else:
        st.info("Pick an API family and endpoint from the sidebar to begin.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Write the thin entrypoint app_v2.py**

Create `app_v2.py`:
```python
from seo_analyser.ui.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the app and smoke-test**

Run:
```bash
streamlit run app_v2.py
```
Expected: app loads; sidebar shows 13 families; selecting `serp` → `google_organic_live_advanced` renders a form with many fields. With valid creds in `.env.local`, filling `keyword`, `location_name`, `language_name` and clicking **Run** returns JSON with SERP results. **This is the Phase 1 acceptance check.**

- [ ] **Step 7: Commit**

```bash
git add seo_analyser/ui app_v2.py
git commit -m "feat: generic endpoint runner UI (Phase 1 acceptance)"
```

---

## Task 9: Run the full test suite

- [ ] **Step 1: Run all tests**

Run:
```bash
pytest -v
```
Expected: all tests across `test_introspect.py`, `test_widgets.py`, `test_errors.py` PASS.

- [ ] **Step 2: Commit any fixes**

If fixes were needed:
```bash
git add -A && git commit -m "test: fixes from full suite run"
```

---

## Acceptance summary

- **Phase 0 gate:** `pytest tests/test_introspect.py` passes and `python -m seo_analyser.registry.introspect` prints ~565 endpoints across 13 families with `serp` largest.
- **Phase 1:** `streamlit run app_v2.py` → pick any live endpoint → auto-form → Run → JSON result.
- The old `app.py` is untouched, so `main` remains deployable; `app_v2.py` is the rebuild entrypoint until Phase 5 cutover.

---

## Self-review notes

- **Spec coverage (Phases 0–1):** introspection (Task 2), catalogue (Task 3), type→widget mapping incl. enum/range (Task 4), error normalisation (Task 5), live runner + auth (Task 6), form rendering (Task 7), sidebar picker + raw-JSON result + new entrypoint (Task 8). Fuzzy search, smart rendering, export, task polling, persistence, cost/balance/share/bulk, overrides → deferred to the Phase 2–5 plan, as scoped.
- **`http_path` divergence from spec:** intentionally dropped; documented in File Structure note.
- **Type consistency:** `EndpointMeta` (fields `name`, `family`, `request_model`, `is_task_based`) used identically across introspect/catalogue/live/endpoint_page; `FieldSpec` (`name`, `kind`, `description`, `default`, `choices`, `min`, `max`) used identically across widgets/builder; `RunError` (`kind`, `message`, `status_code`) used identically across errors/live/endpoint_page; `Credentials` (`login`, `password`, `is_complete`) used identically across auth/sidebar/live.
- **Streamlit-dependent code is not unit-tested by design** (spec §4); the testable cores (`fields_for`, `extract_choices`, `extract_range`, `normalise`, `build_catalogue`) all have tests.
