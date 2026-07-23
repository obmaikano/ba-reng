# Ba Reng — Botswana MP Monitor: Architecture & Product Plan

*"Ba reng?" (Setswana, roughly "what are they saying?") — working name for
the platform.*

## 1. Goal
Track every MP's contributions in the National Assembly (questions, motions,
bill participation, committee of supply engagement) from multiple official
sources, and publish it as a public-facing site + social content so citizens
can see what their MP has actually done.

## 2. Data sources

| Source | What it has | Access pattern | Notes |
|---|---|---|---|
| **Botswana Speaks** — `botswanaspeaks.gov.bw/category/4/parliament` | Order Papers, Notice Papers (oral Qs), Committee of Supply speeches, Bills, Motions | HTML listing → article page → linked PDF | Primary source. Richest per-MP detail (name, constituency, ministry, full question text). No API, no pagination params visible — listing appears to return full history on one page; must be verified/handled defensively. |
| **Parliament of Botswana document library** — `parliament.gov.bw/index.php?option=com_documents&view=files&catid=87` | Hansard (verbatim debate transcripts), committee reports | Joomla document manager, likely paginated `catid`/`Itemid` params | Hansard is the gold-standard source for *floor debate* contributions (speeches, interjections) that Notice/Order Papers don't capture — worth adding once oral-question pipeline is stable. |
| **Wikipedia — 13th Parliament of Botswana** | Canonical MP roster: constituency, full name, party | One-off fetch | Used to resolve "MR. T. FURNITURE (TATI EAST)" → "Thabologo Furniture, BCP". Refresh on by-elections/deaths/resignations. |
| **IEC Botswana** (optional) | By-election results, updated seat changes | Periodic check | Keeps roster current between elections. |
| **Party/MP social accounts** (optional, later phase) | Self-reported activity, context | Manual curation or light scraping | Lower priority; used for cross-referencing, not primary record. |

Each source becomes its own **connector module** with a common output shape
(see §5), so adding a new source later doesn't touch the parsing/storage/site
layers.

## 3. High-level architecture

```
                    ┌─────────────────────────┐
                    │   Source Connectors      │
                    │  (one per site/source)   │
                    │  botswanaspeaks_conn.py  │
                    │  parliament_docs_conn.py │
                    │  roster_conn.py          │
                    └───────────┬──────────────┘
                                │ raw documents (HTML/PDF/text) + metadata
                                ▼
                    ┌─────────────────────────┐
                    │   Parsers                │
                    │  - notice_paper parser   │
                    │  - order_paper parser    │
                    │  - hansard parser        │
                    │  - committee_of_supply   │
                    └───────────┬──────────────┘
                                │ structured "Contribution" records
                                ▼
                    ┌─────────────────────────┐
                    │  Entity Resolution       │
                    │  match name+constituency │
                    │  → canonical MP record   │
                    └───────────┬──────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   Datastore (SQLite/     │
                    │   Postgres)              │
                    │  mps, contributions,     │
                    │  documents, sources      │
                    └───────────┬──────────────┘
                                │
                ┌───────────────┼───────────────────┐
                ▼               ▼                    ▼
        ┌───────────────┐ ┌───────────┐     ┌──────────────────┐
        │ Public API     │ │ Static/   │     │ Social publisher  │
        │ (read-only)    │ │ web site  │     │ (drafts posts,    │
        │                │ │ generator │     │ human approves)   │
        └───────────────┘ └───────────┘     └──────────────────┘
                ▲
                │
        ┌───────────────┐
        │  Scheduler     │  (cron / GitHub Actions)
        │  runs crawl →  │
        │  parse → build │
        │  daily         │
        └───────────────┘
```

Key design choice: **crawl/parse is decoupled from serving.** The crawler
writes to the datastore; the site and API just read from it. This means the
crawler can run anywhere with normal internet access (a scheduled job, your
own machine, GitHub Actions) even though the site itself might be static and
hosted elsewhere (Vercel/Netlify/GitHub Pages) or a small API server.

## 4. Data model

**mps**
| field | type | notes |
|---|---|---|
| id | pk | |
| full_name | text | canonical, from roster |
| constituency | text | null for specially-elected |
| party | text | |
| role | text | e.g. "Speaker", "Minister of Finance", null for backbench |
| status | text | active / former (resigned, died, lost by-election) |
| participation_index | derived, not stored raw | computed from contributions table per §8 — a count/weighting of recorded signals, always rendered with the proxy-metric caveat; never derived from or implying attendance |

**documents**
| field | type | notes |
|---|---|---|
| id | pk | |
| source | text | e.g. "botswanaspeaks" |
| source_url | text | article page URL |
| pdf_url | text | |
| doc_type | text | notice_paper / order_paper / committee_of_supply / bill / motion / hansard |
| published_date | date | |
| raw_text_hash | text | to detect re-crawls of unchanged docs |

**contributions**
| field | type | notes |
|---|---|---|
| id | pk | |
| mp_id | fk → mps | nullable until resolved |
| document_id | fk → documents | |
| contribution_type | text | oral_question / motion / bill_reading / committee_of_supply / ministers_question_time |
| date | date | sitting date, not publish date |
| ministry_addressed | text | nullable (not all types target a ministry) |
| subject_text | text | short extracted subject line |
| full_text | text | full question/speech text where available |
| raw_match_name | text | what the parser actually matched, for audit/debugging |

**crawl_runs** (operational log)
| id | started_at | finished_at | source | new_documents | errors |

## 5. Connector → parser contract

Every connector returns a list of:
```
{
  "source": "botswanaspeaks",
  "source_url": "...",
  "pdf_url": "...",
  "title": "...",
  "published_date": "2026-07-13",
  "doc_type_guess": "notice_paper"   # refined later by parser
}
```
Every parser takes raw text + doc_type and returns a list of `Contribution`
dicts matching the schema above, with `raw_match_name` populated so entity
resolution and later auditing both have something to work from.

## 6. Entity resolution

- Primary key: **constituency name** (normalized: lowercase, strip
  punctuation/whitespace variants like "Tlokweng" vs "Tlowkeng" typos seen in
  source data).
- Fallback: **surname match** for specially-elected members (no constituency)
  and for cases where constituency is missing/garbled in the source PDF.
- Unmatched mentions are stored with `mp_id = null` and flagged in a review
  queue rather than silently dropped or guessed — bad matches are worse than
  no match on a public accountability site.

## 7. API (read-only, public)

```
GET /api/mps                          list all MPs, with contribution counts
GET /api/mps/{id}                     MP profile + summary stats
GET /api/mps/{id}/contributions       paginated, filterable by type/date range
GET /api/constituencies/{name}        resolve constituency → MP
GET /api/contributions                global feed, filterable by type/ministry/date
GET /api/contributions/{id}           full text + source document link
GET /api/search?q=                    full-text search across subjects
```
Simple, cacheable, versionless-for-now REST API. Every contribution links
back to the original PDF/source URL — the site should never present a
paraphrase as if it were the primary record.

## 8. Metrics — what we can and can't honestly measure

**No attendance register exists.** Unlike South Africa (ParliMeter gets a real
attendance feed from PMG) or the UK (division/roll-call data), Botswana's
Parliament does not publish who was physically present on a given sitting
day. Order Papers list scheduled business; they are not a roll call. Hansard
records what was said, not who stayed silent in the chamber. This means:

- **Do not build or label anything "Attendance Tracker."** That would imply
  we know who showed up, which we don't — a false claim would be a real
  credibility and possibly legal problem for a site whose whole purpose is
  factual accountability.
- **Build a "Participation Index" instead** — a proxy metric, explicitly
  labeled as a proxy, built only from things an MP is on the record as
  having done:

| Signal | Source | What it tells you |
|---|---|---|
| Oral question asked | Notice Paper | MP was present and active that sitting |
| Motion moved / seconded | Order Paper | MP was present and active that sitting |
| Bill contribution (2nd reading debate, committee stage) | Hansard | MP was present and spoke |
| Committee of Supply intervention (non-Minister MPs questioning a vote) | Hansard | MP was present and active |
| Sitting days with *zero* recorded signal for an MP | derived | **Cannot be read as "absent."** MPs do committee work, constituency work, and silent-but-present participation (seconding without speaking, voting by voice) that leaves no document trail. Flag as "no recorded activity," never as "absent" or "did not attend."

**Every MP profile and every leaderboard view must carry a visible
methodology note** along the lines of: *"This reflects recorded contributions
in official Parliament documents, not physical attendance — Botswana's
Parliament does not publish attendance records. A low count may mean low
participation, or it may mean a document type we don't yet cover (e.g.
committee proceedings) captured that MP's work instead."* This isn't
boilerplate — it's the difference between a fair accountability tool and one
that unfairly brands quiet-but-diligent MPs as absent.

**If you later want real attendance data**, the only legitimate path is
requesting it directly from the Clerk of the National Assembly / Hansard
office as a public records request — worth a mention on the About page as
"we've requested attendance data and will add it if released," which also
puts gentle public pressure on Parliament to publish it (this is exactly how
Mzalendo's public gap-shaming of Kenya's official site worked).

## 9. Public site — UI plan

**Home / feed**
- Chronological feed of recent contributions across all MPs (like a news feed)
- Filters: constituency, party, ministry, contribution type, date range

**MP profile page** (`/mp/tati-east` or `/mp/thabologo-furniture`)
- Header: photo placeholder, name, constituency, party, role
- Stats: total contributions this session, breakdown by type, most-addressed ministries
- Timeline: every contribution, newest first, each linking to source PDF
- "Compare" affordance: pick another MP to compare activity levels

**Constituency lookup**
- Search/select a constituency → jump to that MP's profile
- Useful for "find my MP" entry point

**Leaderboard / transparency views**
- Participation Index ranking (most/least recorded contributions by count) —
  titled and captioned as a proxy, per §8, never as "most/least active" or
  anything implying attendance
- Ministries most frequently questioned
- MPs with zero recorded contributions this session — shown with the same
  "no recorded activity ≠ absent" caveat inline, not just on a separate About
  page, since this is the view most likely to be screenshotted out of context

**About / methodology page**
- Explicitly states sources, crawl frequency, known limitations, and a
  correction-request mechanism — essential for credibility on a site that
  publicly evaluates elected officials.

## 10. Social publishing

- A scheduled job diffs "contributions added since last run" and generates
  draft posts (e.g. "🏛️ MP Kapinga (Okavango West) asked the Minister of
  Environment & Tourism about Mohembo bridge development — [link]").
- **Human-in-the-loop by default**: drafts go to a review queue (could be as
  simple as a private channel/spreadsheet) before anything posts, at least
  until the parser's accuracy is well-proven. Misattributing a quote to the
  wrong MP on a public accountability account is a real reputational and
  legal risk.

## 11. Scheduling / "keeping it live"

Since this environment can't run a persistent background job, the crawl
needs to run somewhere with normal (unrestricted) internet access:
- **GitHub Actions** (simplest, free tier is enough for a daily crawl):
  workflow runs crawler → updates DB/JSON → rebuilds static site → deploys
  (e.g. to GitHub Pages or Vercel).
- or a small always-on host (a $5/mo VM) running a cron job if you want a
  live API rather than a static site.

## 12. Comparable platforms (context)

No dedicated Botswana platform exists yet. The closest models, and what to
borrow from each:

- **TheyWorkForYou (UK) / Pombola (mySociety's open-source engine)** — the
  reference architecture: a structured MP↔constituency↔party↔contributions
  database. Powers Mzalendo (Kenya), People's Assembly (South Africa, run by
  PMG), Odekro (Ghana), KuvakaZim (Zimbabwe). Worth reviewing Pombola's schema
  on GitHub (`mysociety/pombola`) even without reusing the Django codebase.
- **ParliMeter (South Africa, 2025, OUTA/OpenUp/PMG)** — closest in ambition
  to "everything," including attendance and bill tracking. Its attendance
  tracker works *because* PMG has a real attendance feed from Parliament —
  Botswana doesn't have the equivalent, which is why §8 replaces that with a
  Participation Index instead of copying this feature directly.
- **Mzalendo (Kenya)** — notable precedent: its independently-maintained MP
  database was *more* accurate than Kenya's official parliamentary site,
  which had stale constituency boundaries and was missing over half its MPs.
  A useful argument for why this project has value even though Parliament of
  Botswana already publishes its own documents.
- **abgeordnetenwatch.de (Germany)** — adds a responsiveness layer: citizens
  publicly ask MPs questions and the site tracks whether they reply. Worth
  considering for a later phase, separate from the core contributions record.

## 13. Open questions to settle before build

1. **Scope of "everything"**: confirm Hansard (floor debate) is in scope for
   a later phase, since it's a much heavier parsing job than Order/Notice
   Papers (free-form speech transcripts vs. structured question lists).
2. **Hosting**: static site (cheap, simple, great for a feed/profile site) vs
   a small server (needed only if you want live search/filtering beyond what
   a static site + client-side JS can do).
3. **Legal/ethical**: this is public parliamentary record, which is fine to
   republish, but the "leaderboard" and "zero contributions" framing should
   be reviewed for fairness (e.g. new MPs, MPs in non-vocal committee roles)
   before going live, so it doesn't misrepresent quieter-but-active MPs.
4. **Update cadence**: daily is almost certainly enough given the sitting
   calendar; no need for anything more frequent.
5. **Branding**: name settled — "Ba Reng." Still to confirm before public
   launch: `bareng.bw` / `bareng.org.bw` availability via nic.net.bw
   (BOCRA's registrar, first-come-first-served, no residency requirement),
   matching social handles, and a quick check that no existing Botswana
   org/app already uses the name.

## 14. Administration & RBAC

### 14.1 Three roles

| Role | Abilities |
|---|---|
| **Admin** | Full system control — manage users, trigger crawls, resolve entities, view logs, delete data |
| **Editor** | Resolve entity matches, flag/review contributions, view system health. No user management or crawl control |
| **Viewer** | Read-only access to system health dashboard, data quality stats. No write actions |

### 14.2 Auth

Email + password authentication. JWT tokens (24h expiry) stored in httpOnly cookies. `passlib` + `bcrypt` for password hashing. SQLite session store.

### 14.3 Admin Screens

| Screen | Route | Access |
|---|---|---|
| Admin Dashboard | `/admin` | Viewer+ |
| Entity Review Queue | `/admin/entities` | Editor+ |
| User Management | `/admin/users` | Admin only |
| Crawl Log | `/admin/crawls` | Admin only |
| Contribution Review | `/admin/contributions` | Editor+ |

Integrated in same React app under `/admin/*`. Route-guarded by React Router with role-checking `ProtectedRoute` component.

## 15. Suggested build order

1. Botswana Speaks connector + Notice Paper parser (oral questions only) —
   highest value, cleanest structure, proves the entity-resolution approach.
2. Entity resolution against the roster + review-queue for unmatched names.
3. SQLite store + minimal read-only API.
4. Static site: feed + MP profile pages.
5. Order Paper / Committee of Supply / Bills parsers (broaden coverage).
6. GitHub Actions scheduling for "live" updates.
7. Social draft-post generator (human-approved).
8. Hansard connector (floor speeches) — biggest lift, do last.
