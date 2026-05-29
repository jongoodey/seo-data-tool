# Current App Audit — `app.py`

**Purpose:** Detailed inventory of everything in the existing monolithic `app.py` so we can decide what to salvage, what to discard, and what patterns to preserve in the rebuild.

**File:** `/Users/jongoodey/Sites/tools/ai-overviews/app.py`
**Total lines:** 3,550
**Language:** Python 3.9+, Streamlit 1.32
**Last meaningful change:** Initial commit + Railway deployment (2 commits total)

---

## 1. File layout at a glance

| Lines       | Section                                  | Lines | %     |
|-------------|------------------------------------------|-------|-------|
| 1–15        | Imports + page config                    | 15    | 0.4%  |
| 17–622      | `DataForSEOClient` class (30 methods)    | 605   | 17%   |
| 623–742     | Helper functions (4 helpers)             | 119   | 3%    |
| 744–3548    | `main()` — sidebar + per-endpoint branches | 2,804 | 79%   |
| 3549–3550   | `__main__` entrypoint                    | 2     | 0%    |

Almost 80% of the file is one function. That's the single biggest architectural problem.

---

## 2. Imports

```python
streamlit as st
pandas as pd
plotly.express as px
plotly.graph_objects as go
from datetime import datetime
import requests
import base64
import json
```

No SDK dependency yet — raw `requests` everywhere. No typing, no pydantic, no logger, no test framework. That's fine for the current scope but won't scale.

---

## 3. `DataForSEOClient` class (lines 17–622)

A thin HTTP client. Constructor stores login + password; `_get_auth_header()` returns the HTTP Basic header. Every endpoint method follows the same shape:

```python
def get_<endpoint>(self, ...args):
    endpoint = f"{self.base_url}/<path>"
    payload = [{"key": val, ...}]
    try:
        response = requests.post(endpoint, json=payload, headers=self._get_auth_header())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
```

### 3.1 Method inventory

| Lines     | Method                                  | Endpoint hit                                                       | Notes                                                |
|-----------|-----------------------------------------|--------------------------------------------------------------------|------------------------------------------------------|
| 31–51     | `get_keyword_search_volume`             | `/ai_optimization/ai_keyword_data/keywords_search_volume/live`     | AI Optimisation v3                                   |
| 53–82     | `get_llm_response`                      | `/ai_optimization/chat_gpt/llm_responses/live`                     | Note: hits `chat_gpt` sub-path regardless of model    |
| 84–110    | `get_google_ai_overview`                | `/serp/google/ai_mode/live/advanced`                               | Surfaces as AI overview but actually `ai_mode`        |
| 112–145   | `_get_country_code` (helper, not API)   | local map                                                          | 29 hardcoded countries; defaults to `"US"` on miss   |
| 149–173   | `get_backlinks`                         | `/backlinks/backlinks/live`                                        |                                                      |
| 175–192   | `get_broken_backlinks`                  | `/backlinks/backlinks/live`                                        | Same endpoint, filter `[["is_lost","=",True]]`        |
| 194–213   | `get_backlink_anchors`                  | `/backlinks/anchors/live`                                          |                                                      |
| 215–234   | `get_referring_domains`                 | `/backlinks/referring_domains/live`                                |                                                      |
| 236–251   | `get_backlink_summary`                  | `/backlinks/summary/live`                                          |                                                      |
| 253–265   | `get_bulk_backlinks`                    | `/backlinks/bulk_backlinks/live`                                   |                                                      |
| 267–279   | `get_bulk_referring_domains`            | `/backlinks/bulk_referring_domains/live`                           |                                                      |
| 281–293   | `get_bulk_ranks`                        | `/backlinks/bulk_ranks/live`                                       |                                                      |
| 295–307   | `get_bulk_spam_score`                   | `/backlinks/bulk_spam_score/live`                                  |                                                      |
| 309–323   | `get_bulk_new_lost_backlinks`           | `/backlinks/bulk_new_lost_backlinks/live`                          |                                                      |
| 325–341   | `get_bulk_new_lost_referring_domains`   | `/backlinks/bulk_new_lost_referring_domains/live`                  |                                                      |
| 343–361   | `get_serp_organic`                      | `/serp/google/organic/live/advanced`                               |                                                      |
| 363–386   | `get_bulk_serp`                         | `/serp/google/organic/live/advanced`                               | Loops over keywords client-side (no real bulk)        |
| 388–404   | `get_domain_rank_overview`              | `/dataforseo_labs/google/domain_rank_overview/live`                |                                                      |
| 406–427   | `get_historical_rank_overview`          | `/dataforseo_labs/google/historical_rank_overview/live`            |                                                      |
| 429–449   | `get_ranked_keywords`                   | `/dataforseo_labs/google/ranked_keywords/live`                     |                                                      |
| 451–469   | `get_keyword_suggestions`               | `/dataforseo_labs/google/keyword_suggestions/live`                 |                                                      |
| 471–488   | `get_keyword_ideas`                     | `/dataforseo_labs/google/keyword_ideas/live`                       |                                                      |
| 490–507   | `get_keywords_for_site`                 | `/dataforseo_labs/google/keywords_for_site/live`                   |                                                      |
| 509–526   | `get_keywords_for_categories`           | `/dataforseo_labs/google/keywords_for_categories/live`             |                                                      |
| 528–543   | `get_search_intent`                     | `/dataforseo_labs/google/search_intent/live`                       |                                                      |
| 545–563   | `get_bulk_keyword_difficulty`           | `/dataforseo_labs/google/bulk_keyword_difficulty/live`             |                                                      |
| 565–581   | `get_google_search_volume`              | `/keywords_data/google_ads/search_volume/live`                     |                                                      |
| 583–601   | `get_bing_search_volume`                | `/keywords_data/bing/search_volume/live`                           |                                                      |
| 603–621   | `get_instant_pages`                     | `/on_page/instant_pages`                                           | Sole on-page endpoint                                 |

**Count:** 29 endpoint methods + 1 helper. The README says "3 features" — that's wildly out of date.

### 3.2 Response transformations

None of the client methods reshape responses. They just `return response.json()`. All transformation happens in `main()` per-endpoint. That's good news for the rebuild — the client layer is pure pass-through and can be replaced by the SDK without losing logic.

### 3.3 Error handling

Every method has the same `try / except RequestException` block that calls `st.error(...)` and returns `None`. Coupling the HTTP client to the Streamlit UI like this means:

- Can't reuse the client outside Streamlit
- Can't test without mocking Streamlit
- Same error message regardless of failure mode (timeout vs 4xx vs 5xx)
- No retry, no backoff, no rate-limit handling

**Salvage decision:** discard the entire class. The PythonClient SDK replaces every method, handles auth, and centralises error types properly.

---

## 4. Helper functions (lines 623–742)

### 4.1 `parse_keyword_data(response_data)` — lines 623–651

Takes the AI keyword search volume response and flattens it to a DataFrame. Extracts:

- `Keyword`, `Current Search Volume`, `Location`, `Language`
- 12 historical columns named `SV_YYYY-MM` from `ai_monthly_searches[-12:]`

The flattening pattern (drilling through `tasks → result → items → ai_monthly_searches`) is the same pattern repeated 29 times in `main()` with different field names. It's a textbook case for one generic flattener.

### 4.2 `create_trend_chart(df, keyword)` — lines 653–684

Plotly `go.Scatter` line+marker chart for a single keyword's monthly SV. Blue line (`#1f77b4`), markers size 8, height 400, hovermode `x unified`.

### 4.3 `create_comparison_chart(df)` — lines 686–703

Plotly Express bar chart. Sorted by SV descending, colour-graded by SV with the `Blues` continuous scale, height 400.

### 4.4 `create_trend_comparison_chart(df)` — lines 705–742

Multi-line `go.Scatter` chart — one trace per keyword, legend on the right (`xanchor='right', x=1.15`), height 500.

**Salvage decision:** keep all four as the *seeds* of the smart-result renderers. The trend chart is generic enough to apply to any endpoint with `ai_monthly_searches`-shaped data; the bar chart works for any list of `{label, value}` pairs.

---

## 5. Sidebar config (lines 749–820)

Lives in `with st.sidebar:`. Three sections:

### 5.1 API Credentials (lines 752–754)
```python
api_login = st.text_input("DataForSEO Login", type="default")
api_password = st.text_input("DataForSEO Password", type="password")
```
No "remember for session", no auto-fill from env, no validation. Re-typing on every refresh.

### 5.2 Analysis Settings (lines 758–800)

Two-level selector:

1. **Category** — `["AI Optimisation", "Backlinks", "SERP & Rankings", "Keywords"]`
2. **Function** — different list per category, total ~30 functions

No search, no filter. Adding a new endpoint means editing this list AND adding an `elif function_type ==` branch deep in `main()` 800 lines below.

### 5.3 Location + Language (lines 803–820)

Hardcoded lists:

- **Locations** (29): United States, United Kingdom, Canada, Australia, Germany, France, Spain, Italy, Netherlands, Belgium, Switzerland, Austria, Sweden, Norway, Denmark, Finland, Poland, Czech Republic, Ireland, Portugal, Greece, Japan, South Korea, Singapore, India, Brazil, Mexico, Argentina, Chile
- **Languages** (17): English, Spanish, French, German, Italian, Portuguese, Dutch, Polish, Swedish, Norwegian, Danish, Finnish, Czech, Greek, Japanese, Korean, Chinese

DataForSEO actually publishes endpoint-specific location and language tables — `serp/google/locations` and `serp/google/languages` return hundreds. The current app uses 29 generic names that may not match every endpoint exactly.

The `_get_country_code` map (lines 112–145) is a parallel table that maps these names to ISO codes for `web_search_country_iso_code` in the LLM scraper. Duplication waiting to drift.

### 5.4 Credential gate (lines 822–835)

If creds aren't filled, shows a warning, the "How to use this tool" markdown, and returns early. Standard pattern.

---

## 6. Per-endpoint UI branches (lines 841–3537)

The body of `main()` is one giant `if function_type == ... elif ... elif ...` chain. 29 branches, each implementing the same five-step pattern:

```
1. st.header() with emoji
2. Form widgets (st.text_input / st.text_area / st.selectbox / etc.)
3. st.button(type="primary")
4. On click: validation → st.spinner → client.<method> → response check
5. If success: st.metric(s) → build DataFrame → tabs (Data | Charts | Export)
```

### 6.1 Sample: AI Keyword Search Volume (lines 841–954)

- Widgets: one big `st.text_area` for keywords
- Validation: at least one keyword; cap at 1000 unique
- Metrics: 4 `st.metric` calls (Total Keywords, Total SV, Avg, Highest)
- Tabs: 4 — Overview / Trends / Data Table / Export
- Charts: comparison bar (Tab 1), multi-line trend + per-keyword trend (Tab 2)
- Exports: CSV + JSON

### 6.2 Sample: LLM Scraper (lines 956–1402)

- Widgets: SE selector (4 options), force_web_search toggle, prompt text_area (500 char cap), expander for Temperature slider + Max Tokens number_input + System Message
- Internal model_map: ChatGPT → `gpt-4o`, Claude → `claude-3-5-sonnet-20241022`, Gemini → `gemini-1.5-pro`, Perplexity → `sonar-reasoning` (drift target — Sonnet 3.5 is already historic)
- Response display: tries 4 different shapes (`item['sections']`, `item['content']['sections']`, `item['text']`, `item['message']` / `item['response']`) — symptom of API returning different shapes per LLM, papered over with branching
- Exports: full JSON only

### 6.3 Sample: Backlink List (lines 1423–1556)

- Widgets: target text_input, mode selectbox (as_is / one_per_domain / one_per_anchor), limit number_input (1–1000), status selectbox (live / lost / all), include_subdomains checkbox
- Metrics: 4 — Total / Returned / Target / Cost (USD)
- DataFrame columns: 11 hand-picked fields
- Tabs: Data Table | Charts | Export
- Charts: pie (dofollow vs nofollow), horizontal bar (top 20 referring domains)
- Exports: CSV + JSON

### 6.4 The repeated pattern in code

```python
elif function_type == "X":
    st.header("emoji X")
    # widgets...
    if st.button("Action"):
        if not validate: return
        with st.spinner("..."):
            response = client.get_x(...)
        if response and 'tasks' in response and response['tasks']:
            task = response['tasks'][0]
            if task['status_code'] == 20000 and task.get('result'):
                result = task['result'][0]
                st.success(f"Found {result.get('total_count', 0):,}!")
                # 1-4 st.metric calls
                if 'items' in result and result['items']:
                    rows = []
                    for item in result['items']:
                        rows.append({...hand-picked fields...})
                    df = pd.DataFrame(rows)
                    tab1, tab2, tab3 = st.tabs(["📋 Data", "📊 Charts", "💾 Export"])
                    with tab1: st.dataframe(df, use_container_width=True, hide_index=True)
                    with tab2: # 1-3 plotly charts
                    with tab3: # CSV + sometimes JSON download_buttons
            else:
                st.error(f"Error: {task.get('status_message', 'Unknown error')}")
```

This is the entire repeated template. The variation across branches is:

- Which input widgets appear
- Which fields get picked from `item`
- Which chart types render in tab 2
- Whether 1, 2, 3, or 4 tabs exist

**Salvage decision:** this template IS the universal renderer. The auto-generated rebuild reproduces this exact flow once and lets endpoint metadata drive the variation.

### 6.5 Special-case: hardcoded category map (lines 3445–3472)

The "Keyword Suggestions for Categories" branch carries its own dict of 25 category names → numeric codes (e.g. `"Apparel": 10166`). DataForSEO publishes the full ~600-entry category tree via the API but the app hardcodes 25. Drift risk.

---

## 7. UX polish worth preserving

Things the existing app does well that the rebuild should keep:

| What                                  | Where                                | Why                                                              |
|---------------------------------------|--------------------------------------|------------------------------------------------------------------|
| Emoji-prefixed section headers        | Throughout                           | Scannable; helps at-a-glance navigation between tools             |
| 4-up `st.metric` row                  | AI keyword (l. 880), backlinks (l. 1483) | Consistent summary statistics — generalise to "show top-level numeric fields from response" |
| Cost surfaced in metric               | Backlinks (l. 1491–1492)             | Pulls `task['cost']` and shows it — useful for credit-conscious users; bake into universal results header |
| `use_container_width=True` everywhere | All charts + dataframes              | Right default for a wide layout                                  |
| `hide_index=True` on st.dataframe     | All tables                           | Cleaner; should be the default in renderer                       |
| `download_button` filename with timestamp | All exports                      | Avoids overwrite confusion                                       |
| Help-text on every input              | All forms                            | Keep — pull from SDK field descriptions (rich source)             |
| Spinner during fetch                  | All endpoints                        | Standard UX                                                       |
| Bar + line + pie variety              | Across endpoints                     | Generalise into shape-detection renderer                          |
| Inputs in `st.columns()` rows         | Most endpoints                       | Compact form layout — should be default                          |

---

## 8. Code smells / debt

| Issue                                                        | Lines              | Severity | Fix in rebuild                                                  |
|--------------------------------------------------------------|--------------------|----------|------------------------------------------------------------------|
| One 2,800-line `main()` function                             | 744–3548           | Critical | Modular structure (see overview §5.1)                            |
| 29× duplicated response-parsing block                        | Throughout main()  | High     | Single universal parser in `runner/`                             |
| `st.error()` called inside HTTP client                       | Every client method| High     | Decouple — client raises typed exceptions, UI catches             |
| Hardcoded location list mismatches API truth                 | 803–810, 112–145   | Medium   | Fetch dynamically from `serp/google/locations`, cache             |
| Hardcoded language list mismatches API truth                 | 814–820            | Medium   | Same — fetch from `/serp/google/languages`                        |
| `_get_country_code` parallel to location list                | 112–145            | Medium   | Replace with single canonical lookup                              |
| 25-entry category map duplicates an API-served catalogue     | 3445–3472          | Medium   | Fetch from API; cache                                             |
| LLM model names baked into code                              | 1027–1032          | Medium   | These will rot (Claude 3.5 Sonnet is already historic). Pull from DataForSEO's models endpoint |
| 4-way response shape fallback for LLM Scraper                | 1072–1099          | Medium   | Auto-detection renderer handles this generically                  |
| No tests anywhere                                            | n/a                | High     | Add unit tests for registry, form builder, result detector        |
| README out of date — claims 3 features, app has 29           | README.md          | Low      | Regenerate from registry catalogue                                |
| Credentials re-prompt every refresh                          | 752–754            | Low      | Session-scoped storage                                            |
| `get_bulk_serp` loops client-side instead of using bulk API  | 363–386            | Low      | SDK / proper bulk endpoint                                        |
| No retry / backoff                                           | All client methods | Low      | SDK handles via urllib3; expose timeout config                    |
| No request/response logging                                  | n/a                | Low      | Add Python logger; surface "last request" in dev mode             |
| `category_codes=[category_options[cat] for cat in selected_categories]` reads from outer dict | 3492 | Low | Style only |
| `style=unsafe_allow_html=True` footer                         | 3540–3547          | Trivial  | Use `st.caption` or `st.markdown` without HTML                    |
| No `.gitignore` for `__pycache__`                             | repo root          | Trivial  | Standard hygiene                                                  |

---

## 9. Summary: what survives, what dies

### Dies (full rewrite)
- `DataForSEOClient` class — entirely replaced by `dataforseo-client` SDK
- The 2,800-line `main()` body — replaced by generic endpoint runner
- 29× duplicated response parsers — replaced by one universal flattener
- Hardcoded location / language / category lists — replaced by API-served catalogues
- `_get_country_code` lookup — redundant once we use ISO codes from the API
- README — regenerated from the new architecture

### Survives (folded into rebuild)
- The five-step UX template (header → form → button → spinner → tabbed results)
- Plotly chart styling (colours, heights, hovermode, legend position)
- `st.metric` summary row pattern
- `st.dataframe(use_container_width=True, hide_index=True)` defaults
- Timestamped download filenames
- Emoji-prefixed section headers
- Sidebar layout (creds → settings → location/language picker)
- Cost metric from `task['cost']`

### New
- Endpoint search / fuzzy filter
- Run history + saved presets
- Auto-detected result rendering
- Universal export (CSV / JSON / parquet)
- Per-endpoint YAML overrides for hot endpoints
- Task-based endpoint polling
- Account balance widget
- SQLite persistence (history + presets)

---

## 10. Effort to rebuild vs evolve

Evolving the current file in place would mean:

- Adding ~1,100 more `elif function_type ==` branches
- Each branch is ~50 lines of mostly-duplicated code
- Final `app.py` ≈ 60,000 lines

That's not a viable file. The rebuild is the only path forward; the current 3,550 lines simply can't extend to 100× their current endpoint count.

The good news from this audit: every line of `main()` is a slight variation on the same template, and *all* of the variation lives in metadata (which fields to display, which chart, what to validate). That metadata is exactly what the SDK's Pydantic request models give us for free.
