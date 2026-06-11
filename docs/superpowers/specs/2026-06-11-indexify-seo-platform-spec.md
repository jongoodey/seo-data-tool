# Indexify SEO Platform — Consolidated Product Specification

**Date:** 2026-06-11 · **Status:** agreed direction, prototype-first
**Owner:** Jon Goodey (Indexify)

The working document for merging the SEO Analyzer, the Rank Tracker and a new
conversational layer into one Ahrefs/SEMrush-class product, prototyped privately
first, hardened for clients second.

---

## 1. Vision

One tool where an SEO (from junior to Jon) can:

1. **See** their clients' performance: tracked rankings, AI visibility, trends
   (the Rank Tracker today).
2. **Ask** anything in plain English and have an analyst agent fetch, combine
   and explain the data: chat on the left, live artefacts on the right
   (the DesiMe creator pattern).
3. **Reach** every corner of the DataForSEO API when the curated views aren't
   enough (the SEO Analyzer today).
4. **Blend in their own Google data** (Search Console, GA4, Google Ads) via
   their own OAuth grant, so the agent reasons over rankings *and* clicks
   *and* spend together.

Differentiators vs Ahrefs/SEMrush: AI visibility tracking (already built),
a chat analyst with *complete* API coverage (no other tool exposes everything),
the client's own Google data in the same conversation, and radical cost
transparency (every call priced before and after — already the analyzer's DNA).

## 2. The three assets being merged

| Asset | Stack | Role in the platform |
|---|---|---|
| **SEO Analyzer** (`~/Sites/tools/ai-overviews`) | Python/Streamlit, Railway, Postgres | Becomes the **engine**: catalogue of 396 operations, runner, results parsing, cost ledger. Streamlit UI stays as the internal lab. |
| **Rank Tracker** (`~/Sites/tools/rank-tracker`) | React 18 + Chakra (Vite), Express, SQLite | Becomes the **product shell**: clients, auth, dashboards, scheduling, AI visibility. Gains the chat pane. |
| **DesiMe Social Creator** (`~/Sites/clients/desime/Social-media-creator---Desime`) | Next.js + Anthropic tool-use | **Reference pattern only** (no code merge): chat thread + artefact-driven canvas, sparse update tools, inline-editable cards, progress-as-chat-messages. |

What we copy from DesiMe: `useChatPipeline`-style orchestration, artefact chips
in chat that open canvas tabs, sparse tool updates, per-item progress cards.
What we fix from DesiMe (its known weaknesses): **stream** responses (SSE),
keep ONE artefact store keyed by id instead of duplicating state between chat
and canvas, let chat trigger any canvas action (no canvas-only buttons).

## 3. Target architecture (one Railway project)

```
Railway project "intuitive-transformation"
├── web      — Rank Tracker (React+Chakra SPA served by Express)
│              + NEW chat pane (SSE client) + canvas artefact tabs
├── engine   — NEW Python FastAPI service, lifted from seo_analyser/ core:
│              /catalogue  endpoint metadata as JSON (from introspection)
│              /run        execute any endpoint (validated, costed, logged)
│              /agent      the analyst loop (Anthropic tool-use, SSE out)
│              /mcp        same tool registry exposed as an MCP server
├── analyzer — existing Streamlit app (internal lab; retire when ready)
└── postgres — ONE database for everything
```

Why the engine is Python and stays Python: the 396 auto-generated forms/tools
come from introspecting the DataForSEO Python SDK's Pydantic models
(`seo_analyser/registry/introspect.py`). That introspection is the platform's
crown jewel; it emits **Claude tool schemas and React form schemas for free**.
`seo_analyser`'s registry/runner/results/billing modules already have no
Streamlit imports and 100+ tests — they lift into FastAPI nearly unchanged.

Why the product shell stays React/Express for now: 5,300 working backend lines
and 41 components exist today. Rewriting buys nothing user-visible. Revisit
only if two backend languages become a genuine maintenance pain.

### Platform decision: Railway (not Vercel, not Netlify)

- The engine is long-running Python with an agent loop and SSE streaming —
  a poor fit for Vercel/Netlify serverless functions (timeouts, cold starts,
  no resident process). Railway runs resident services natively.
- Postgres, domains, env vars and deploy-on-push are already set up there.
- The scheduler (rank fetches, AI visibility sweeps) needs a resident cron
  process — again natural on Railway, awkward on edge platforms.
- Vercel/Netlify remain the right choice for the future *marketing site*
  (static, SEO-critical), which should live separately anyway.

Domains when ready: `app.indexify.co.uk` (product) and
`analyzer.indexify.co.uk` (internal lab).

## 4. The chat layer ("the Analyst")

**Where it runs:** the engine service (Python, Anthropic SDK), because the
engine owns the tool registry. The web service just renders the stream.

**Model:** Claude Sonnet (claude-sonnet-4-6) per message by default; allow an
"Opus moment" escalation for complex multi-step analyses later. Token spend is
logged per chat session alongside DataForSEO spend — one ledger, two currencies.

**The tool registry — three rings:**

1. **Curated tools (~15-20):** hand-picked, beautifully described, mapped to
   the endpoints juniors actually need: `serp_snapshot`, `keyword_ideas`,
   `keyword_volumes`, `ranked_keywords`, `backlinks_summary`, `competitors`,
   `ai_visibility_mentions`, `page_audit`, `track_keywords` (writes to the
   tracker), `rankings_history` (reads the tracker's own data) etc.
2. **The escape hatch:** one generic `run_dataforseo(endpoint, params)` tool,
   validated against the auto-generated catalogue schemas, so the agent can
   reach all 396 operations when a curated tool doesn't fit.
3. **Google tools** (per connected workspace): `gsc_search_analytics`,
   `ga4_run_report`, `ads_campaign_stats`.

**"Knows what questions to ask":** encoded in the system prompt + a planning
habit: before answering, the agent states what data it needs, checks what the
workspace already has (recent runs are cached — re-use, don't re-buy), asks
the user only when intent is genuinely ambiguous, and proposes follow-ups
("I have rankings but no click data — connect Search Console and I can show
you where you rank well but get no clicks").

**Cost guardrails (non-negotiable, from day one):**
- Every tool call priced before execution; calls estimated above a per-call
  threshold (default $0.10) require explicit user confirmation in chat.
- Per-session and per-workspace spend budgets; the agent sees remaining budget.
- Every call logged to the unified `api_runs` ledger with `chat_session_id`.

**MCP exposure:** the same registry served over MCP from `engine /mcp`. Jon can
plug the whole platform into Claude Desktop/Code immediately; later it becomes
a customer feature. One registry, two consumers — no double maintenance.

### Chat + canvas UX (the DesiMe pattern, improved)

- Left: chat thread. Right: canvas with artefact tabs (Table, Chart, Report,
  Raw). Tool results become **artefacts** stored once, by id; chat messages
  carry artefact chips that focus the canvas.
- Artefacts are interactive: sortable tables, CSV download, "pin to client
  dashboard", "open in power tools" (deep link to the full endpoint form).
- Streaming SSE so long analyses feel alive; per-tool progress rendered as
  inline progress cards (DesiMe's nicest trick).
- Everything the chat can do is also clickable manually, and vice versa —
  the chat is a layer over the product, never a silo.

## 5. Google integrations (user's own credentials)

**Flow:** standard OAuth 2.0 web flow with offline access, per workspace.
"Connect Google" button → consent → tokens stored server-side. Scopes,
read-only: `webmasters.readonly` (GSC), `analytics.readonly` (GA4); Google Ads
read scope later (requires a developer-token application to Google — **apply
early**, basic access covers own accounts which is fine for the prototype).

**Storage (Postgres):**
- `google_connections`: id, workspace_id, google_email, scopes,
  `refresh_token_enc` (AES-256-GCM, key in `TOKEN_ENCRYPTION_KEY` env var,
  never logged), created/updated.
- `google_properties`: connection_id, kind (gsc_site | ga4_property |
  ads_customer), external_id, display_name, client_id (maps a property to a
  tracker client so the agent knows whose data is whose).
- Access tokens cached in memory only; refresh on demand.
- Tokens never enter the chat context — the agent calls tools, tools hold creds.

**Prototype:** Jon's own Google Cloud project, OAuth consent screen in testing
mode (his Google accounts only), redirect URI on the Railway domain.

## 6. Data model changes (one Postgres)

New/unified tables (tracker's 12 SQLite tables migrate as-is, then):

- `users`, `workspaces` (tracker "clients" become workspaces), `memberships`
  (user × workspace × role) — multi-tenant from the start, even with one user.
- `api_runs` — unified ledger replacing the analyzer's `runs` and the
  tracker's fetch logs: endpoint, params, cost, status, source
  (`chat` | `ui` | `schedule` | `lab`), workspace_id, chat_session_id nullable.
- `chat_sessions`, `chat_messages` (role, content jsonb incl. tool calls,
  artefact refs), `artifacts` (id, workspace_id, type, payload jsonb, pinned).
- `google_connections`, `google_properties` (above).
- `spend_budgets` (workspace_id, period, dataforseo_cap, llm_token_cap).

## 7. UI layer principles

Carry the junior-SEO lessons (they're proven now — yesterday's audit pass):

1. **Task-shaped entry points** everywhere; API vocabulary never required.
2. **Plain English errors** with the fix in the message.
3. **No paid call without informed intent** — price shown before, actual after.
4. **No dead ends** — every screen offers the next step (the prereq panel and
   Home button are the pattern).
5. **Empty states teach**: a new workspace shows "Add your client's domain →
   track 10 keywords → connect Search Console", not a blank table.
6. Onboarding in three steps, each skippable; chat available from second one.
7. Keep Chakra UI for now (it's what the tracker uses; consistent and fast).
   Indexify brand tokens (colours, type) applied across web + analyzer theme.
   A Tailwind/shadcn refresh is a later cosmetic decision, not structural.

## 8. Phasing

### Phase A — private prototype (Jon only, existing keys, ~2 weeks)

Explicitly accepted for the prototype: current credentials and the private
repo stay as they are (rotation deferred — see the hard gate below).

- **A1. Engine service** (2-3 days): lift `seo_analyser` core into FastAPI
  (`/catalogue`, `/run`); internal bearer token between web and engine;
  deploy as second Railway service sharing the existing Postgres.
- **A2. Tracker → Postgres + same Railway project** (1 day): SQLite schema
  ports cleanly; secrets to env vars (values unchanged for now).
- **A3. Chat MVP** (3-4 days): `/agent` SSE loop with ring-1 curated tools +
  the generic escape hatch; two-pane UI in the tracker (ChatThread,
  MessageBubble, CanvasPanel ported from the DesiMe pattern, with streaming
  and the single artefact store); cost guardrails on.
- **A4. Google read-only** (2-3 days): OAuth flow, encrypted token storage,
  GSC + GA4 tools, property→client mapping UI. (Ads tool lands whenever the
  developer token arrives — submit the application during A1.)

Exit criteria: Jon runs a real client review end-to-end in chat — rankings
trend + GSC clicks + AI visibility + a keyword-ideas artefact pinned to the
client dashboard — for under $0.50 of API spend.

### Phase B — client-facing hardening (the gate, ~1 week)

**Hard gate before ANY non-Jon user touches it:**
- Rotate **all** credentials (DataForSEO, JWT secret, Google client secret,
  APP_PASSWORD) and purge `.env` from the rank-tracker git history
  (`git filter-repo`). This is deferred from today by Jon's explicit choice;
  it stops being optional the moment a second person gets a URL.
- Real accounts: signup/invite, password reset, workspace roles enforced
  server-side on every route; per-workspace data isolation tests.
- Spend caps enforced per workspace; rate limiting; audit log review.
- Remove every Jon-specific assumption (default admin user, hardcoded ports).

### Phase C — commercial layer (~1-2 weeks, when B is done)

- **Stripe**: subscriptions (Starter/Pro/Agency) + metered usage billed from
  the `api_runs` ledger — the cost data is already perfect for this.
- Two key models: **BYO keys** (customer's DataForSEO/Anthropic keys, cheaper
  plan) and **platform keys** (we carry the keys, meter with margin).
- Transactional email (Resend), usage alerts at 80% of caps, status page.

## 9. Open questions for Jon

1. Product name (affects domain; "SEO Analyzer" and "Rank Tracker" are both
   working titles, neither is the product).
2. Who is user #2 — an Indexify teammate, or a friendly client? (Shapes how
   hard Phase B needs to be before first feedback.)
3. Google Ads priority: worth the developer-token wait, or GSC+GA4 enough for
   the prototype?
4. Chat default model: Sonnet for everything, or Opus for analysis-heavy
   requests at higher cost?

## 10. Immediate next actions

1. Submit the Google Ads API developer-token application (longest lead time).
2. Create the Google Cloud OAuth client (testing mode) for the prototype.
3. A1: scaffold the engine service from `seo_analyser` core and deploy it
   alongside the analyzer.
4. A2: tracker SQLite → Postgres migration script + Railway service.
5. Write the Phase A implementation plan (same handover format as
   `2026-06-10-junior-seo-ux-handover.md`) once Jon answers §9.
