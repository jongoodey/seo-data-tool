# DataForSEO PythonClient SDK — Technical Feasibility Analysis

**Purpose:** Confirm that the official `dataforseo-client` SDK is the right engine to drive an auto-generated Streamlit UI. Stress-test the introspection plan against real SDK code before committing.

**SDK repo:** https://github.com/dataforseo/PythonClient
**SDK package:** [`dataforseo-client` on PyPI](https://pypi.org/project/dataforseo-client/)
**Code generation:** OpenAPI Generator CLI from a master OpenAPI 3.1 YAML spec (https://github.com/dataforseo/OpenApiDocumentation)
**Python:** 3.9+ (uses `typing_extensions.Self`, Pydantic v2)

---

## 1. Verdict up front

**It works.** The SDK exposes everything needed to auto-generate forms:

- Every endpoint is a method on an `Api` class
- Every request payload is a **Pydantic v2 `BaseModel`** with typed, optional fields
- Every field carries a `Field(description=...)` lifted from DataForSEO's own documentation
- The list of all endpoints is enumerable by iterating the SDK's `api` submodule

Two concerns require handling but are manageable:

1. **Each public endpoint exposes three method variants** — must filter to the canonical one
2. **Some request fields use nested model types** — need recursive form rendering

Both are addressed in §6 and §7 below.

---

## 2. SDK structure

```
dataforseo_client/
├── __init__.py
├── api_client.py             # HTTP client, request dispatcher
├── api_response.py
├── configuration.py          # auth, host, SSL, proxy, retries
├── exceptions.py             # typed exceptions
├── rest.py                   # urllib3 wrapper
├── api/                      # 13 modules, one per API family
│   ├── serp_api.py
│   ├── keywords_data_api.py
│   ├── backlinks_api.py
│   ├── dataforseo_labs_api.py
│   ├── on_page_api.py
│   ├── domain_analytics_api.py
│   ├── content_analysis_api.py
│   ├── content_generation_api.py
│   ├── merchant_api.py
│   ├── app_data_api.py
│   ├── business_data_api.py
│   ├── ai_optimization_api.py
│   └── appendix_api.py
└── models/                   # 1,000+ Pydantic models (requests + responses)
```

The `api/` directory contains the 13 API-family classes; `models/` contains every request model, response model, and nested model (~1,000 files).

---

## 3. Auth

```python
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider
from dataforseo_client.api.serp_api import SerpApi

configuration = dfs_config.Configuration(username='USERNAME', password='PASSWORD')
with dfs_api_provider.ApiClient(configuration) as api_client:
    serp_api = SerpApi(api_client)
```

HTTP Basic, same as today. The `Configuration` class also exposes proxy, SSL, retries, logging — all settable from the sidebar if we want power-user mode.

---

## 4. Endpoint methods — three flavours per endpoint

The SDK generator emits **three method variants** for each endpoint, e.g. for `google_organic_live_advanced`:

| Variant                                            | Purpose                                                | We use it? |
|----------------------------------------------------|--------------------------------------------------------|------------|
| `google_organic_live_advanced(req)`                | Returns the parsed response model                      | **Yes**    |
| `google_organic_live_advanced_with_http_info(req)` | Returns response + headers + status                    | No         |
| `google_organic_live_advanced_without_preload_content(req)` | Returns the raw urllib3 response (for streaming) | No         |

`SerpApi` alone has 543 methods, but 543 / 3 = **181 canonical endpoints**.

Filter rule for the registry: keep methods that don't end in `_with_http_info` or `_without_preload_content`. The remaining methods are the user-facing endpoints.

---

## 5. Request models — confirmed Pydantic v2

Real example. The request payload for `serp.google_organic_live_advanced` is the class `SerpGoogleOrganicLiveAdvancedRequestInfo`:

```python
class SerpGoogleOrganicLiveAdvancedRequestInfo(BaseModel):
    keyword: Optional[StrictStr] = Field(default=None, description=r"keyword required field...")
    location_code: Optional[StrictInt] = Field(default=None, description=r"search engine location code...")
    language_code: Optional[StrictStr] = Field(default=None, description=r"...")
    depth: Optional[StrictInt] = Field(default=None, description=r"parsing depth...max value: 200...")
    device: Optional[StrictStr] = Field(default=None, description=r"...desktop, mobile...")
    load_async_ai_overview: Optional[StrictBool] = Field(default=None, description=r"...you will be charged extra $0.002...")
    location_name: Optional[StrictStr] = Field(default=None, description=r"...")
    language_name: Optional[StrictStr] = Field(default=None, description=r"...")
    os: Optional[StrictStr] = Field(default=None, description=r"...desktop: windows, macos. mobile: android, ios...")
    tag: Optional[StrictStr] = Field(default=None, description=r"user-defined task identifier...")
    stop_crawl_on_match: Optional[List[Optional[SerpApiStopCrawlOnMatchInfo]]] = Field(...)
    match_type: Optional[StrictStr] = Field(default=None, description=r"...domain – specific domain or subdomain | with_subdomains | wildcard...")
    match_value: Optional[StrictStr] = Field(...)
    max_crawl_pages: Optional[StrictInt] = Field(default=None, description=r"...max value: 100...")
    search_param: Optional[StrictStr] = Field(...)
    remove_from_url: Optional[List[Optional[StrictStr]]] = Field(...)
    people_also_ask_click_depth: Optional[StrictInt] = Field(default=None, description=r"...possible values: from 1 to 4")
    group_organic_results: Optional[StrictBool] = Field(default=None, description=r"...default value: true")
    calculate_rectangles: Optional[StrictBool] = Field(default=None, description=r"...you will be charged extra $0.002...")
    browser_screen_width: Optional[StrictInt] = Field(default=None, description=r"...range: 240-9999...default: 1920 desktop, 360 mobile android, 375 mobile iOS")
    browser_screen_height: Optional[StrictInt] = Field(...)
    browser_screen_resolution_ratio: Optional[StrictInt] = Field(default=None, description=r"...range: 0.5-3...")
    url: Optional[StrictStr] = Field(...)
    location_coordinate: Optional[StrictStr] = Field(default=None, description=r"...latitude,longitude,radius format...")
    se_domain: Optional[StrictStr] = Field(...)
    target: Optional[StrictStr] = Field(...)
    target_search_mode: Optional[StrictStr] = Field(default=None, description=r"...all, any. default: any")
    find_targets_in: Optional[List[Optional[StrictStr]]] = Field(...)
    ignore_targets_in: Optional[List[Optional[StrictStr]]] = Field(...)
```

That's **29 fields** vs the **6** the current app exposes. Auto-generation gives users the full surface for free.

### 5.1 Field metadata available via introspection

| Pydantic mechanism                    | What we get                                                                |
|---------------------------------------|----------------------------------------------------------------------------|
| `Model.model_fields`                  | Dict of `{field_name: FieldInfo}` for every field                          |
| `FieldInfo.annotation`                | Resolved type (e.g. `Optional[StrictInt]`, `List[NestedModel]`)            |
| `FieldInfo.description`               | The full description string from `Field(description=...)`                  |
| `FieldInfo.default`                   | Default value (often `None`, sometimes a literal)                          |
| `Model.__name__`                      | Stable class name we can store in the catalogue                            |
| `model_dump(exclude_none=True)`       | Round-trip serialisation, so a form-filled instance → JSON for the request |

The descriptions are dense (concatenated sentences without newlines), but they include:

- Required/optional status
- Default values
- Min/max ranges
- Enum members ("possible values: a, b, c")
- **Pricing modifiers** ("you will be charged extra $0.002 for using this parameter")
- Mutual-exclusion rules ("if you specify X, you don't need to specify Y")

We can use them verbatim as Streamlit help text and parse them progressively (e.g. extract enum lists) for richer widgets.

---

## 6. Type → widget mapping

Every field type maps cleanly to a Streamlit widget:

| Pydantic type                                | Widget                                                         | Notes                                                       |
|----------------------------------------------|----------------------------------------------------------------|-------------------------------------------------------------|
| `Optional[StrictStr]`                        | `st.text_input`                                                | If description contains "possible values: a, b, c" → `st.selectbox(["a", "b", "c"])` |
| `Optional[StrictInt]`                        | `st.number_input(min=, max=, step=1)`                          | Parse range from description if present                     |
| `Optional[StrictFloat]`                      | `st.number_input(format="%.4f")` or `st.slider`                | Slider for known-bounded floats (e.g. temperature 0-2)      |
| `Optional[StrictBool]`                       | `st.checkbox`                                                  | Default from `FieldInfo.default`                            |
| `Optional[List[StrictStr]]`                  | `st.text_area` → split on newlines/commas                      | Same UX as current keyword input                            |
| `Optional[List[StrictInt]]`                  | `st.text_area` → parse to ints                                 |                                                             |
| `Optional[List[NestedModel]]`                | Recursive: render a "+ Add" button that opens a sub-form       | See §7                                                      |
| Date strings (e.g. `date_from`)              | `st.date_input` → ISO string                                   | Detect by field name or description hints                   |
| Coordinate strings (`location_coordinate`)   | `st.text_input` with placeholder example                        | Could become 3 inputs (lat, lon, radius) if we want polish  |

### 6.1 Enum extraction from descriptions

DataForSEO encodes enums in plain prose. We can pattern-match the common forms:

- `"possible values: a, b, c"`
- `"can take the values: a, b, c"`
- `"choose from the following values: a, b, c"`

A regex `r"possible values:?\s*([a-z_, ]+)"` covers ~80% of fields. The rest stay as free-text inputs — acceptable for v1, upgrade later.

### 6.2 Range extraction

Patterns like:

- `"max value: 200"` → `max_value=200`
- `"range: 240-9999"` → `min=240, max=9999`
- `"from 1 to 4"` → `min=1, max=4`

Same approach: regex out the common shapes, fall back to unbounded.

---

## 7. Nested models

Some request fields are `List[NestedModel]` — e.g. `stop_crawl_on_match: Optional[List[Optional[SerpApiStopCrawlOnMatchInfo]]]`.

A nested model is just another `BaseModel`, so the form builder recurses:

1. Render a collapsible "Stop crawl on match" section
2. Show "+ Add target" button
3. For each added entry, render the nested model's fields (recursively, but in practice 1-2 levels deep)
4. Collect into a list on submit

For v1 we can hide all nested-model fields behind an "Advanced" expander to keep the default form clean.

---

## 8. Live vs task-based endpoints

DataForSEO endpoints split into two flavours:

### 8.1 Live endpoints

Single round-trip. Form submit → SDK call → response → render. Behaves identically to the current app.

```python
response = serp_api.google_organic_live_advanced([request_model])
```

### 8.2 Task-based endpoints

Three steps:

1. **Post**: `serp_api.google_organic_task_post([request])` returns `task_id`
2. **Poll**: `serp_api.google_organic_tasks_ready()` lists ready tasks
3. **Get**: `serp_api.google_organic_task_get_advanced(id=task_id)` returns the result

This pattern appears across SERP, Backlinks, On-Page, App Data, and others — usually for crawls that take seconds-to-minutes.

### 8.3 UI abstraction

The auto-generated UI treats a `task_post / tasks_ready / task_get_*` triplet as **one logical endpoint**:

1. Form takes the union of fields that the `task_post` request needs
2. On submit: post task, store `task_id` in `st.session_state`, show spinner + elapsed time
3. Poll every 5s via `tasks_ready`; UI auto-refreshes via `st.empty()` placeholders or `st.experimental_rerun()`
4. When ready: call the matching `task_get_advanced` (preferred) or `task_get_regular`, render the result
5. Cancel button removes the task from session_state but does not cancel server-side (DataForSEO has no cancel API)

Registry metadata stores `is_task_based: True` and the three method names per endpoint.

### 8.4 What about HTML / regular / advanced variants?

Some endpoints have multiple `task_get` flavours (`_advanced`, `_regular`, `_html`). Default: prefer `_advanced` (richest payload). Expose a "Response format" selector in the overrides YAML if the endpoint warrants it.

---

## 9. Catalogue construction (pseudocode for the spec — not for implementation now)

```
import inspect
import importlib
import pkgutil
import dataforseo_client.api as api_pkg
from pydantic import BaseModel

catalogue = {}

for _, mod_name, _ in pkgutil.iter_modules(api_pkg.__path__):
    module = importlib.import_module(f"dataforseo_client.api.{mod_name}")
    # the Api class is the one ending in "Api"
    api_class = next(c for name, c in inspect.getmembers(module, inspect.isclass)
                     if name.endswith("Api") and c.__module__ == module.__name__)

    family = mod_name.replace("_api", "")
    catalogue[family] = []

    for method_name, method in inspect.getmembers(api_class, inspect.isfunction):
        # skip private / variants / dunders
        if method_name.startswith("_") or method_name.endswith("_with_http_info") \
           or method_name.endswith("_without_preload_content"):
            continue

        sig = inspect.signature(method)
        # request model is the parameter whose annotation is a BaseModel subclass
        request_model = next(
            (p.annotation for p in sig.parameters.values()
             if hasattr(p.annotation, "__origin__") or
                (inspect.isclass(p.annotation) and issubclass(p.annotation, BaseModel))),
            None
        )

        is_task_based = method_name.endswith("_task_post")

        catalogue[family].append({
            "name": method_name,
            "request_model": request_model.__name__ if request_model else None,
            "is_task_based": is_task_based,
            "docstring": (method.__doc__ or "").strip(),
        })
```

That builds a catalogue dict of every endpoint in the SDK, with the introspection metadata for forms. Cache it as JSON for fast Streamlit startup; rebuild only when the SDK version changes.

---

## 10. Risks identified

| Risk                                                       | Likelihood | Impact | Mitigation                                                           |
|------------------------------------------------------------|------------|--------|-----------------------------------------------------------------------|
| Some endpoints take POST bodies as `List[Model]` (current uses `[{...}]`) | High | Low | Already standard — wrap single requests in `[...]`. SDK does this for us. |
| Field descriptions don't follow uniform format             | Certain    | Medium | Accept partial enum/range extraction; fall back to free-text input    |
| Nested models 2-3 levels deep create wide, confusing forms | Medium     | Medium | Hide behind "Advanced" expander; document override hooks               |
| SDK version drift between releases                         | Low–medium | Medium | Pin SDK version in requirements.txt; surface SDK version in sidebar    |
| New endpoint type appears that doesn't fit live/task model | Low        | High   | Defer until it happens; current 1,130 endpoints all fit                |
| Task-based polling adds Streamlit reruns / state complexity| Medium     | Medium | Wrap in a dedicated component with clear UX (spinner, cancel, elapsed) |
| Some endpoints have no introspectable request model (GET-only) | Medium | Low | Detect; render no form, just a Run button. Common for `*_locations`, `*_languages` listing endpoints |
| Pydantic version compatibility (SDK uses v2)               | Low        | High   | Pin pydantic >=2 in requirements; conflicts unlikely with Streamlit    |

---

## 11. Confidence summary

| Aspect                                | Confidence | Evidence                                                              |
|---------------------------------------|------------|-----------------------------------------------------------------------|
| SDK covers all 1,130 endpoints        | High       | 13 API modules in `api/`, generated from official OpenAPI YAML        |
| Models are introspectable             | Certain    | Verified Pydantic v2 BaseModel with `Field(description=...)` patterns |
| Auto-generated forms will work for ~95% of fields | High | Common type set (`StrictStr/Int/Bool/Float`, `Optional`, `List`) |
| Auto-generated forms will work for nested models  | Medium | Need recursive renderer; doable but adds code                    |
| Description text usable for help + enum extraction| Medium | Verbose but regex-friendly for common patterns                   |
| Task-based UX                         | Medium     | Standard polling pattern; Streamlit reruns require care               |
| BYOK auth                             | Certain    | `Configuration(username, password)` — identical to current model      |
| Pricing surfacing                     | Medium     | Sometimes in description strings; full pricing requires separate fetch from DataForSEO docs |
| Result rendering across all endpoints | Medium–High | Smart-detect handles ~90%; per-endpoint overrides cover the rest |

---

## 12. What this means for the design

This analysis confirms:

- The proposed architecture in `seo-analyser-overview.md` §5 is technically feasible
- We don't need to write or maintain endpoint definitions ourselves — the SDK is authoritative
- Risk lives mainly in the **UX** layer (nested model forms, enum extraction, task polling) not the **data** layer
- Switching to the SDK eliminates all of the current app's hand-rolled HTTP + auth code

The next document, `endpoint-inventory.md`, lists the actual endpoints we'll be exposing so we can spot any patterns we missed.
