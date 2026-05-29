# SEO Analyzer Tool — Documentation Index

**Status:** Analysis phase — no implementation yet
**Date:** 2026-05-29
**Owner:** Jon Goodey (Indexify)

This folder is the planning and analysis record for the rebuild from "AI Keyword Analyser" to a bring-your-own-key universal gateway over the full DataForSEO API.

---

## Read order

If you're catching up cold, read these in order:

1. **`seo-analyser-overview.md`** — strategic overview, decisions locked, proposed architecture, phased plan, open questions
2. **`current-app-audit.md`** — detailed audit of the existing `app.py`: every endpoint method, every UI branch, what to salvage, what to discard
3. **`endpoint-inventory.md`** — full inventory of the 565 DataForSEO endpoints, organised by API family, with priority tiers for v1 rollout
4. **`sdk-technical-analysis.md`** — verifies the auto-generation approach against the real SDK code; type→widget mapping; risks

If you already know the project: skim the overview's §4 (decisions locked) and §7 (open decisions) to see where we are.

---

## One-paragraph summary

The current app exposes ~30 of DataForSEO's 565 endpoints behind 2,800 lines of hand-rolled Streamlit forms. The rebuild replaces all of it with: (1) the official `dataforseo-client` PythonClient SDK as the source of endpoint definitions, (2) an introspection layer that walks the SDK and builds a catalogue of every endpoint's Pydantic request model, (3) a generic form builder that maps Pydantic types to Streamlit widgets, (4) a smart result renderer that auto-detects response shapes, and (5) per-endpoint YAML overrides for the ~30 endpoints that already have polished UX worth preserving. The framework stays Streamlit; deploys stay on Railway; auth stays BYOK.

---

## Decision status

| Locked                                                 | Open                                       |
|--------------------------------------------------------|--------------------------------------------|
| Auto-generated forms (not hand-rolled)                 | Cost preview per call in v1?               |
| `dataforseo-client` SDK as source of truth             | Account balance widget?                    |
| Clean rebuild, keep Streamlit, keep Railway            | Shareable URL state encoding?              |
| Smart auto-detection result rendering                  | Bulk-from-CSV in v1 or v2?                 |
| Run history + saved presets in v1                     | Client workspaces?                         |
| Product name: "SEO Analyzer Tool"                      | Persistence layer: SQLite vs in-memory?    |
| Endpoint search baseline (required at this scale)      | Seed overrides.yml with the existing 30?   |
| CSV + JSON export baseline                            | Feature branch swap, or in-place rebuild?  |

Defaults for the open decisions are recorded in `seo-analyser-overview.md` §7.

---

## What's NOT in this folder

- No code (analysis phase only)
- No implementation plan (next step, after open decisions are locked)
- No tests, no scaffolds, no commits to `app.py`

The implementation plan lands at `docs/superpowers/specs/2026-05-29-seo-analyser-design.md` once the open decisions are resolved.

---

## Quick stats from the analysis

| Stat                                       | Value                                                       |
|--------------------------------------------|-------------------------------------------------------------|
| Current `app.py` total lines               | 3,550                                                       |
| Lines inside one `main()` function         | 2,804 (79% of file)                                         |
| Endpoint methods on `DataForSEOClient`     | 29                                                          |
| Hardcoded location names                   | 29 (vs hundreds in API)                                     |
| Hardcoded language names                   | 17                                                          |
| Hardcoded category codes                   | 25 (vs ~600 in API)                                         |
| DataForSEO endpoints total                 | **565**                                                     |
| DataForSEO API families                    | 13                                                          |
| Largest family (SERP)                      | 181 endpoints                                               |
| Smallest family (Appendix)                 | 4 endpoints                                                 |
| Current coverage                           | **5%** of DataForSEO (29 / 565)                             |
| Target v1 coverage                         | **100%** via auto-generation                                |
| Lines if we hand-coded all 565 endpoints   | ~60,000 (untenable)                                         |
| SDK request models                         | All Pydantic v2 BaseModels with `Field(description=...)`    |
| SDK auth                                   | HTTP Basic — same as today                                  |
| Tests in the current app                   | 0                                                           |
