# DataForSEO Endpoint Inventory

**Purpose:** Concrete inventory of what we'll be exposing. Counts and groupings drawn from the official `dataforseo-client` SDK's published markdown docs (counted live from the SDK repo).

**Total unique HTTP endpoints across 13 API families:** **565**

> **Note on the count:** the previous overview document quoted ~1,130 endpoints. That figure double-counted endpoints that appear in multiple SDK doc tables. The real, deduplicated count from the SDK's URI tables is **565**.
>
> In the SDK's Python code each endpoint is exposed as **three method variants** (`endpoint`, `endpoint_with_http_info`, `endpoint_without_preload_content`), which is where the 1,500+ method count comes from. From the UI's perspective there are 565 things to render.
>
> Many task-based endpoints come in triplets (`task_post` + `tasks_ready` + `task_get_*`). The runner treats each triplet as **one logical operation**, so the user-facing operation count is closer to **~350–400**.

---

## 1. Distribution by API family

| #  | Family             | Endpoints | % of total | What it covers                                                                |
|----|--------------------|-----------|------------|--------------------------------------------------------------------------------|
| 1  | SERP               | 181       | 32%        | Search engine results for 7 engines (Google, Bing, Baidu, Naver, Seznam, Yahoo, YouTube) |
| 2  | Keywords Data      | 70        | 12%        | Google Ads, Bing Ads, Google Trends, DataForSEO Trends, Clickstream            |
| 3  | Business Data      | 55        | 10%        | Google My Business, Tripadvisor, Trustpilot, social media signals              |
| 4  | DataForSEO Labs    | 47        | 8%         | Keyword research, ranked keywords, competitor analysis (Google + Amazon + Apple) |
| 5  | AI Optimization    | 44        | 8%         | LLM responses (ChatGPT, Claude, Gemini, Perplexity), LLM mentions, AI search volume |
| 6  | App Data           | 42        | 7%         | Apple App Store + Google Play apps, reviews, rankings                          |
| 7  | Merchant           | 32        | 6%         | Amazon products, ASIN, sellers + Google Shopping                                |
| 8  | On-Page            | 31        | 5%         | Site crawls, instant page checks, lighthouse, duplicates, raw HTML              |
| 9  | Backlinks          | 24        | 4%         | Anchors, referring domains, summary, bulk metrics, page/domain intersection     |
| 10 | Domain Analytics   | 14        | 2%         | Technology stack detection, Whois                                               |
| 11 | Content Analysis   | 11        | 2%         | Mention search, phrase trends, sentiment, ratings, categories                   |
| 12 | Content Generation | 10        | 2%         | Text generation, paraphrase, meta tag generation, grammar check                 |
| 13 | Appendix           | 4         | 1%         | User data, status, webhook resend, errors                                       |
|    | **Total**          | **565**   |            |                                                                                |

---

## 2. SERP API — 181 endpoints

Largest family by far. Subdivides by search engine:

| Search engine | Endpoints | What's available                                                          |
|---------------|-----------|----------------------------------------------------------------------------|
| Google        | 105       | Organic, AI mode, news, local finder, images, finance, maps, jobs, events, dataset search/info, autocomplete, search by image, ads (search + advertisers), locations, languages |
| YouTube       | 23        | Video search, channels, comments, transcripts                              |
| Yahoo         | 12        | Organic + auxiliary                                                        |
| Bing          | 12        | Organic + auxiliary                                                        |
| Seznam        | 9         | Czech search engine                                                        |
| Baidu         | 9         | Chinese search engine                                                      |
| Naver         | 6         | Korean search engine                                                       |
| **Family-level** | 5     | `ai_summary`, `id_list`, `errors`, `screenshot`, `tasks_ready`             |

### 2.1 Google SERP breakdown (the 105)

| Sub-endpoint            | Count | Notes                                                                  |
|-------------------------|-------|------------------------------------------------------------------------|
| organic                 | 9     | live (regular / advanced / html) + task triplet for each = 9            |
| ai_mode                 | 8     | Google AI Mode SERP — the modern "AI Overview" search                  |
| news                    | 7     |                                                                        |
| local_finder            | 7     |                                                                        |
| images                  | 7     |                                                                        |
| finance_quote           | 6     |                                                                        |
| finance_markets         | 6     |                                                                        |
| finance_explore         | 6     |                                                                        |
| maps                    | 5     |                                                                        |
| jobs                    | 5     |                                                                        |
| events                  | 5     |                                                                        |
| dataset_search          | 5     |                                                                        |
| dataset_info            | 5     |                                                                        |
| autocomplete            | 5     | Keyword autocomplete suggestions                                       |
| search_by_image         | 4     | Image-based search                                                     |
| finance_ticker_search   | 4     |                                                                        |
| ads_search              | 4     | Paid SERP results                                                      |
| ads_advertisers         | 4     | Advertiser metadata                                                    |
| locations               | 2     | List + by-country lookup                                               |
| languages               | 1     |                                                                        |

The current app uses **1** of these (organic + ai_mode). Auto-generation gives us 103 more.

---

## 3. Keywords Data API — 70 endpoints

| Sub-family           | What it does                                                          |
|----------------------|------------------------------------------------------------------------|
| `google_ads`         | Search volume, ad traffic estimation, keyword suggestions from Google Ads |
| `google_trends`      | Trends data — interest over time, regional interest, related queries  |
| `dataforseo_trends`  | DataForSEO's proprietary trends (broader, deeper history than Google) |
| `bing`               | Bing Ads-equivalent data                                              |
| `clickstream_data`   | Clickstream-derived search volume + traffic estimates                 |
| `id_list`, `errors`  | Task / error utilities                                                |

Current app uses **2** (`google_ads/search_volume`, `bing/search_volume`).

---

## 4. Business Data API — 55 endpoints

| Sub-family            | What it covers                                                       |
|-----------------------|----------------------------------------------------------------------|
| `google`              | Google My Business profile data, reviews, hotel search, Q&A          |
| `trustpilot`          | Trustpilot business profiles + reviews                               |
| `tripadvisor`         | Tripadvisor venues + reviews                                         |
| `social_media`        | Facebook, Pinterest, Reddit signals                                  |
| `business_listings`   | Generic business listing search                                      |
| `id_list`, `errors`, `tasks_ready` | task utilities                                          |

Current app: **0**. Whole family is greenfield.

---

## 5. DataForSEO Labs API — 47 endpoints

DataForSEO's enriched SEO data layer.

| Sub-family            | What it covers                                                                       |
|-----------------------|--------------------------------------------------------------------------------------|
| `google`              | Ranked keywords, keyword ideas, suggestions, related keywords, keyword overview, search intent, competitor analysis, traffic estimation, historical keyword/rank data, SERP competitors, domain intersection, page intersection, relevant pages, top searches, subdomains |
| `amazon`              | Amazon-specific keyword research                                                     |
| `apple`               | App Store keyword research                                                           |
| `categories`          | Category catalogue                                                                   |
| `locations_and_languages` | Available locations / languages                                                  |
| `available_filters`   | Per-endpoint filter options                                                          |
| `status`, `id_list`, `errors` | Utility                                                                       |

Current app uses **8** (suggestions, ideas, keywords_for_site, keywords_for_categories, search_intent, bulk_keyword_difficulty, ranked_keywords, domain_rank_overview, historical_rank_overview). Plenty more available.

---

## 6. AI Optimization API — 44 endpoints

| Sub-family       | What it covers                                                                    |
|------------------|------------------------------------------------------------------------------------|
| `ai_keyword_data`| AI search volume per keyword (the metric the current app surfaces)                |
| `chat_gpt`       | Query GPT models with web search                                                  |
| `claude`         | Query Claude models                                                               |
| `gemini`         | Query Gemini models                                                               |
| `perplexity`     | Query Perplexity                                                                  |
| `llm_mentions`   | Track brand/domain mentions across LLM responses (aggregate metrics, top domains, top pages, cross-aggregate metrics) |

Current app uses **3** (keywords_search_volume, chat_gpt/llm_responses, the AI mode SERP under SERP family — not strictly AI Opt). LLM mentions is the high-leverage greenfield area for Indexify.

---

## 7. App Data API — 42 endpoints

| Sub-family | What it covers                                              |
|------------|--------------------------------------------------------------|
| `apple`    | App Store: app info, search, listings, reviews, categories  |
| `google`   | Google Play: same surface                                   |
| `errors`, `id_list`, `tasks_ready` | utility                              |

Current app: **0**.

---

## 8. Merchant API — 32 endpoints

| Sub-family | What it covers                                                          |
|------------|--------------------------------------------------------------------------|
| `amazon`   | Product search (by keyword), ASIN lookup, seller lookup, product reviews |
| `google`   | Google Shopping product feeds                                            |

Current app: **0**. Useful for e-commerce clients (Signature Cashmere, DesiMe).

---

## 9. On-Page API — 31 endpoints

Site auditing surface.

| Sub-endpoint                | What it does                                                  |
|-----------------------------|---------------------------------------------------------------|
| `task_post` + `tasks_ready` | Start and check a site crawl                                  |
| `instant_pages`             | One-off page audit (current app uses this)                    |
| `lighthouse`                | Run Lighthouse on a URL                                       |
| `content_parsing`           | Parse and extract page content                                |
| `raw_html`                  | Fetch raw HTML                                                |
| `page_screenshot`           | Screenshot a URL                                              |
| `pages`, `pages_by_resource`| List crawled pages                                            |
| `resources`                 | List page resources (scripts, images, CSS)                    |
| `links`                     | Outgoing/incoming links per page                              |
| `redirect_chains`           | Follow redirect chains                                        |
| `duplicate_content`         | Find duplicate content across crawl                           |
| `duplicate_tags`            | Find duplicate meta tags                                      |
| `non_indexable`             | List pages blocked from indexing                              |
| `microdata`                 | Extract structured data                                       |
| `keyword_density`           | Keyword density per page                                      |
| `waterfall`                 | Resource load waterfall                                       |
| `summary`                   | Crawl summary                                                  |
| `force_stop`                | Stop a running crawl                                          |
| `uncrawlable_resources`     | List resources that couldn't be crawled                       |
| `available_filters`         | Filter catalogue                                              |
| `errors`, `id_list`         | Utility                                                        |

Current app uses **1** (`instant_pages`). On-Page is the highest-value greenfield family for client SEO audits.

---

## 10. Backlinks API — 24 endpoints

| Sub-endpoint                  | Current app | What it does                              |
|-------------------------------|-------------|-------------------------------------------|
| `backlinks`                   | ✅           | Backlink list                             |
| `anchors`                     | ✅           | Anchor text distribution                   |
| `referring_domains`           | ✅           | Domain-level summary                      |
| `summary`                     | ✅           | Top-level metrics for a target            |
| `bulk_backlinks`              | ✅           | Bulk lookup                               |
| `bulk_referring_domains`      | ✅           |                                           |
| `bulk_ranks`                  | ✅           |                                           |
| `bulk_spam_score`             | ✅           |                                           |
| `bulk_new_lost_backlinks`     | ✅           |                                           |
| `bulk_new_lost_referring_domains` | ✅       |                                           |
| `bulk_pages_summary`          |             | Bulk page-level summary                   |
| `competitors`                 |             | Common referring domains across competitors |
| `domain_intersection`         |             | Domains linking to A but not B            |
| `page_intersection`           |             | Pages linking to multiple targets         |
| `domain_pages`                |             | Pages on the linking domain               |
| `domain_pages_summary`        |             | Aggregate stats for linking domain pages  |
| `referring_networks`          |             | C-class network analysis                  |
| `history`                     |             | Historical backlink counts                |
| `timeseries_summary`          |             | Time-series metrics                       |
| `timeseries_new_lost_summary` |             | Time-series of gains/losses               |
| `index`                       |             | Index status of backlinks                 |
| `available_filters`           |             | Filter catalogue                          |
| `id_list`, `errors`           |             | Utility                                   |

Current app has **10 of 24** (42%). Best-covered family. Missing high-value: `competitors`, `domain_intersection`, `page_intersection`, `referring_networks`, `history`, `timeseries_*`.

---

## 11. Domain Analytics — 14 endpoints

| Sub-family    | What it does                                          |
|---------------|--------------------------------------------------------|
| `technologies`| Detect technologies on a domain (CMS, frameworks, analytics) |
| `whois`       | Whois lookup with metadata                            |
| `errors`, `id_list` | Utility                                          |

Current app: **0**.

---

## 12. Content Analysis — 11 endpoints

| Endpoint           | What it does                                                      |
|--------------------|--------------------------------------------------------------------|
| `search`           | Find mentions of a term across DataForSEO's content index         |
| `phrase_trends`    | Trends of phrase mentions over time                                |
| `summary`          | Aggregate mention metrics                                          |
| `sentiment_analysis`| Sentiment classification on mentions                              |
| `rating_distribution`| Rating histograms                                                |
| `category_trends`  | Trending categories                                                |
| `categories`       | Category catalogue                                                 |
| `locations`        | Locations available                                                |
| `languages`        | Languages available                                                |
| `available_filters`| Filter catalogue                                                   |
| `id_list`          | Utility                                                            |

Current app: **0**.

---

## 13. Content Generation — 10 endpoints

| Endpoint              | What it does                                       |
|-----------------------|----------------------------------------------------|
| `generate`            | Generate text from a prompt                        |
| `generate_text`       | Variant — long-form text                           |
| `generate_meta_tags`  | Title + meta description generation                |
| `generate_sub_topics` | Sub-topic clustering                               |
| `paraphrase`          | Rewrite                                            |
| `text_summary`        | Summarise long text                                |
| `check_grammar`       | Grammar/spell check                                |
| `grammar_rules`       | List of detectable grammar rule types              |

Less critical for SEO but useful for Indexify's content-generation workflows.

---

## 14. Appendix — 4 endpoints

| Endpoint         | What it does                                                                 |
|------------------|------------------------------------------------------------------------------|
| `user_data`      | Account balance, plan, limits — **basis for the balance widget**            |
| `status`         | API health                                                                   |
| `webhook_resend` | Re-fire a webhook for a previous task                                        |
| `errors`         | Account-wide error log                                                       |

---

## 15. Endpoint priority for v1 rollout

The auto-generated approach means we technically expose all 565 simultaneously, but for testing, polish, and documentation, here's a priority ordering:

### Tier 1 — already wired, used by Jon (29 endpoints)

Everything the current app already exposes. These get **bespoke overrides in `overrides.yml`** so their UX doesn't regress (custom charts, polished labels, sensible defaults). See current-app-audit.md §3.1 for the list.

### Tier 2 — high-value greenfield for Indexify (~50 endpoints)

- **Backlinks** missing pieces: `competitors`, `domain_intersection`, `page_intersection`, `history`, `timeseries_*`, `referring_networks`
- **On-Page**: `task_post` crawls, `lighthouse`, `pages`, `redirect_chains`, `duplicate_content`, `duplicate_tags`, `non_indexable`
- **DataForSEO Labs Google**: `relevant_pages`, `subdomains`, `top_searches`, `historical_serp`, `serp_competitors`
- **AI Optimization `llm_mentions`** (8 endpoints): track brand mentions across LLMs — directly aligned with Indexify's marketing-intelligence positioning
- **Content Analysis**: `phrase_trends`, `sentiment_analysis`
- **Domain Analytics**: `technologies`, `whois`
- **Appendix**: `user_data` (drives the balance widget)

### Tier 3 — niche but useful (~100 endpoints)

- **SERP** non-Google: Bing, Baidu, Naver for client-specific markets
- **SERP Google specialised**: news, jobs, events, dataset, autocomplete
- **Merchant Amazon** for e-commerce clients
- **App Data** if any client builds mobile

### Tier 4 — exposed but not curated (~380 endpoints)

Everything else. Auto-generated UI works; no override; users can find via search and run.

---

## 16. Pattern observations across families

| Pattern                                            | Where it appears                              | UI implication                                          |
|----------------------------------------------------|-----------------------------------------------|---------------------------------------------------------|
| Task triplet (`task_post` + `tasks_ready` + `task_get_*`) | SERP, Backlinks, Business Data, App Data, Merchant, On-Page | Treat as one logical endpoint in the UI (see SDK doc §8) |
| `live/regular` vs `live/advanced` vs `live/html`   | SERP                                          | Default to `advanced`; expose format selector in overrides |
| `*_locations` + `*_locations/{country}` + `*_languages` | SERP, Keywords Data, DataForSEO Labs, others | Cache these at startup; use to populate location/language dropdowns dynamically (replaces hardcoded lists) |
| `available_filters`                                | Most families                                 | Use to populate "filter" fields in forms                |
| `id_list`                                          | All families                                  | Could power a "Recent tasks" view in the sidebar        |
| `errors`                                           | All families                                  | Could power a "Recent errors" view                      |
| `categories` catalogue                             | DataForSEO Labs, Content Analysis             | Replaces the 25-entry hardcoded map (current app l. 3445)|

These patterns mean a small set of "support" endpoints (location/language listings, filter catalogues, categories) drive the metadata for the form-builder itself. We should fetch them once on first run, cache the results, and use them to populate dropdowns dynamically.

---

## 17. Estimated DataForSEO costs at scale

Rough order of magnitude based on description-string mentions of pricing in the SDK (full pricing lives at https://dataforseo.com/pricing):

| Endpoint family   | Typical cost per call               |
|-------------------|--------------------------------------|
| SERP live         | $0.0006 – $0.0030 per SERP page      |
| Backlinks live    | $0.02 – $0.10 depending on limit     |
| Keywords Data     | $0.0001 per keyword                  |
| DataForSEO Labs   | $0.01 – $0.05                        |
| AI Optimization (LLM) | $0.005 – $0.05 per LLM response   |
| On-Page instant   | ~$0.0015 per page                    |
| On-Page crawl     | $0.0001 per crawled page             |

So a "run all 565 endpoints once with default params" would cost roughly $5–$20 — which is why **the cost-preview-before-Run feature in the overview's §6.2 is worth doing in v1**, not deferring.

---

## 18. What's still unknown

Open questions this inventory doesn't answer (and that no static analysis can):

- **Per-endpoint actual response shape** — which auto-detect renderer kicks in. We can predict but won't know until we run them.
- **Which endpoints share the same response shape** — likely high overlap, e.g. all SERP organic endpoints return similar structures regardless of engine.
- **Rate limit per endpoint** — some are aggressively rate-limited (the LLM ones especially). We may need backoff / queueing.
- **Which endpoints return empty results that look like errors** — e.g. backlinks for a new domain returns valid response with `items: []`. Renderer needs to distinguish "empty data" from "error".

These all unlock when we run the SDK against real endpoints — not before.

---

## 19. Cross-references

- High-level architecture and decisions: `seo-analyser-overview.md`
- Current app audit (what we're replacing): `current-app-audit.md`
- SDK feasibility deep-dive (how introspection works): `sdk-technical-analysis.md`
