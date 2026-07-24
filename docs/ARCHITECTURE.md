# Ba Reng? — Architecture & Design Specification

*Built from: PLAN.md + Refero Design research + market analysis of 12 comparable platforms*

---

## 1. Reference Lock (Do Not Normalize)

| Decision | Source | Rule |
|---|---|---|
| Canvas `#0B0E14` | Palantir Foundry | Cold slate, not warm dark |
| Type: Inter + JetBrains Mono | Palantir Blueprint | Mono for all metadata, data, tags, timestamps |
| Radius: `0` | Palantir + Refero anti-slop | No rounded corners anywhere |
| Borders: 1px hairline | Palantir Foundry | `#1F242E` subtle, `#2A313D` default |
| Color: functional only | Palantir AIP | Blue = data/metrics, Amber = warnings/unresolved, Green = health, Red = destructive |
| Density: high, table/log views | Palantir + BungeMeter | Scan 42+ rows without scrolling, not card-per-item |
| Imagery: none | Data-infra genre | Data is the visual. MP photos = uniform ratio + monogram fallback |
| Elevation: Blueprint `box-shadow` tokens | Palantir Blueprint BP7 | Inset shadow borders on inputs, elevation shadow on popovers |
| Reject: gradients, shadows, rounded-2xl, warm cream, serif word swaps, animated heroes | Refero anti-slop | Enforced at code review |

---

## 2. Architecture (Updated)

### 2.1 Pipeline

```
                         ┌──────────────────────────────┐
                         │       Source Connectors       │
                         │  botswanaspeaks_conn.py       │
                         │  parliament_docs_conn.py      │
                         │  roster_conn.py               │
                         └─────────────┬────────────────┘
                                       │ raw documents (HTML/PDF/text)
                                       ▼
                         ┌──────────────────────────────┐
                         │    Parsers + Hash Cache       │
                         │  skip unchanged docs via      │
                         │  raw_text_hash on documents   │
                         │  Pipeline per doc_type:       │
                         │  notice_paper | order_paper   │
                         │  committee_of_supply | bill   │
                         │  motion | HANSARD (Regex/NLP) │
                         └─────────────┬────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │                                             │
                ▼                                             ▼
  ┌──────────────────────────┐                  ┌──────────────────────────┐
  │   Entity Resolution      │                  │    Offline spaCy NLP     │
  │ primary: constituency    │                  │  Extract GPE/LOC, MONEY, │
  │ fallback: surname        │                  │  ORG without an LLM      │
  │ unmatched → review queue │                  └─────────────┬────────────┘
  └─────────────┬────────────┘                                │
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                                       ▼
                    ┌────────────────────────────────────┐
                    │          Datastore (SQLite)         │
                    │  mps | documents | contributions   │
                    │  hansard_sessions | agenda_items   │
                    │  utterances | entity_review_queue  │
                    └──────┬──────────────────────┬──────┘
                           │                      │
                           ▼                      ▼
              ┌─────────────────────┐   ┌────────────────────┐
              │   API (read-only)   │   │  Static Site Gen   │
              │   FastAPI            │   │  React + Blueprint │
              │   9 endpoints        │   │  + Vite            │
              └─────────────────────┘   └────────────────────┘

```

### 2.2 Data Model (Changes from PLAN.md)

**mps** — unchanged from PLAN.md. Add `photo_url text nullable` for future official portraits.

**documents** — unchanged.

**contributions** — unchanged.

**entity_review_queue** (new, supports "Unresolved Entities" UI panel):

| field | type | notes |
|---|---|---|
| id | pk | |
| raw_match_name | text | garbled/missing name from parser |
| document_id | fk → documents | source document |
| contribution_id | fk → contributions | link to exact row |
| status | text | UNRESOLVED / IGNORED / RESOLVED |
| resolved_mp_id | fk → mps nullable | admin matched |

**crawl_runs** (expanded for system status bar):

| field | type | notes |
|---|---|---|
| id | pk | |
| started_at | datetime | |
| finished_at | datetime nullable | null while RUNNING |
| source | text | botswanaspeaks / parliament_docs / roster |
| status | text | RUNNING / SUCCESS / FAILED |
| new_documents | int | |
| errors | int | |
| run_type | text | scheduled / manual |

**sit_calendar** (new, from order paper parsing):

| field | type | notes |
|---|---|---|
| id | pk | |
| sitting_date | date | |
| parliament_session | text | e.g. "13th Parliament, 5th Session" |
| source_url | text | order paper URL |

Enables: sitting day counts, "no recorded activity" flags that explicitly show a sitting existed (stronger than "no data").

**hansard_sessions** (new — Hansard free-text transcripts):

| field | type | notes |
|---|---|---|
| session_id | pk (integer) | Auto-incrementing primary key |
| document_id | fk → documents | Link to downloaded PDF document |
| hansard_no | int (unique) | e.g. `221` |
| session_date | date | e.g. `2026-07-14` |
| meeting_description | text | e.g. `Third Meeting of the Second Session of the 13th Parliament` |
| sitting_time | text | e.g. `2:00 p.m.` |

**agenda_items** (new):

| field | type | notes |
|---|---|---|
| agenda_id | pk (integer) | Auto-incrementing primary key |
| session_id | fk → hansard_sessions | Linked session |
| title | text | e.g. `IMPLEMENTATION OF GOVERNMENT REFORMS` |
| category | text | `Questions for Oral Answer`, `Business Motion`, `Speaker's Announcements` |
| sequence_order | int | Section order in the document |

**utterances** (new — Updated with Language & Multilingual Fields):

| field | type | notes |
|---|---|---|
| utterance_id | pk (integer) | Auto-incrementing primary key |
| agenda_id | fk → agenda_items | Linked agenda item / topic |
| mp_id | fk → mps (nullable) | Resolved MP ID |
| speaker_raw_title | text | e.g. `MINISTER FOR STATE PRESIDENT, DEFENCE AND SECURITY` |
| speaker_name | text | e.g. `MR MOHWASA`, `MR PULE` |
| language | text | `en` (English), `tn` (Setswana), or `mixed` (code-switched) |
| speech_type | text | `main_question`, `minister_answer`, `supplementary`, `point_of_order`, `procedural` |
| speech_text | text | Raw speech turn content |
| cleaned_text | text | Speech text with honorifics (`Motlotlegi`, `Rre`) normalized for FTS indexing |
| procedural_notes | text (nullable) | Extracted events e.g. `Applause!`, `Laughter!` |
| extracted_entities | json (nullable) | JSON array: `{"locations": [...], "money": [...], "orgs": [...]}` |
| sequence_order | int | Turn sequence order |

**parliamentary_glossary** (new — Static Terminology Mapping):

| field | type | notes |
|---|---|---|
| id | pk | |
| term_setswana | text (unique) | e.g., `Temothuo`, `Puso`, `Motsamaisa Dipuisanyo`, `Tona` |
| term_english | text | e.g., `Agriculture`, `Government`, `Speaker`, `Minister` |
| category | text | `ministry_keyword`, `title`, `procedural` |

### 2.3 API Surface

```
GET  /api/v1/mps                          → list with contribution counts + participation_index
GET  /api/v1/mps/{id}                     → profile + breakdown by type + timeline
GET  /api/v1/mps/{id}/contributions       → paginated, filterable (?type=&from=&to=)
GET  /api/v1/contributions                → global feed (?ministry=&party=&constituency=)
GET  /api/v1/contributions/{id}           → full text + source doc link
GET  /api/v1/constituencies              → list all, each with current MP
GET  /api/v1/constituencies/{name}        → resolve → MP profile
GET  /api/v1/search?q=                    → full-text across subjects + mp names
GET  /api/v1/status                       → system health (last crawl, unresolved count, doc count)
```

Every response includes `source_url` back to original PDF/document.

---

## 3. Feature Map

### Phase 1 — Core Pipeline (build first)

| Feature | Priority | Depends on | Notes |
|---|---|---|---|
| Botswana Speaks connector | P0 | — | Scrape notice papers for oral questions |
| Notice Paper parser | P0 | connector | Extract structured contributions |
| MP roster from Wikipedia | P0 | — | Canonical MP list with constituency |
| Entity resolution by constituency | P0 | roster + parser | Match name+constituency → MP |
| Entity review queue | P0 | resolution | Store unmatched, surface in UI |
| SQLite store + migration scripts | P0 | — | Single-file, git-versioned |
| Static site: 3-column grid layout | P0 | API/data | Feed + filters + index |
| Live Record Stream (center panel) | P0 | data | Dense table, not cards |
| System status bar (top) | P0 | crawl_runs | Crawler state, error count |
| Participation Index sidebar | P0 | contributions | Top MPs, proxy-metric label |
| Methodology Constraint block | P0 | — | Amber-accented, always visible |
| MP profile page | P0 | mps + contributions | Timeline + stats + source links |
| Constituency lookup / "find my MP" | P0 | mps | Search → constituency → MP profile |
| API: GET /api/v1/mps/contributions/constituencies/search | P1 | — | 7 endpoints |

### Phase 2 — Coverage & Trust

| Feature | Priority | Notes |
|---|---|---|
| Order Paper parser | P1 | Motions, bills, committee of supply |
| Committee of Supply parser | P1 | Budget scrutiny interventions |
| Bill parser | P1 | Bill readings |
| "No recorded activity" flag | P1 | Shown per-MP for sitting days with zero contributions |
| MP-editable review period | P1 | Before public, from Scorecard Nigeria pattern |
| Head-to-head MP comparison | P1 | Side-by-side, from BungeMeter |
| Leaderboard view (proxy) | P1 | Sorted by count, caveat inline |
| Ministries most-questioned | P1 | Derived from contributions.ministry_addressed |
| GitHub Actions schedule | P1 | Daily crawl → build → deploy |

### Phase 3 — Advanced

| Feature | Priority | Notes |
|---|---|---|
| Hansard parser | P2 | Free-form debate transcripts (big lift) |
| Social draft-post generator | P2 | Human-in-loop gate, diff since last run |
| CSV/PDF export on every view | P2 | From BungeMeter pattern |
| Bill tracker with stage timeline | P2 | Parliamentary stage progression |
| AI bill summaries | P2 | From Legis360, CivicAI pattern — only with human review |
| WhatsApp/citizen query layer | P3 | From RAIA pattern, low-priority |
| Promise-vs-delivery tracking | P3 | Cross-ref with manifesto, from CPU Uganda |

---

## 4. UI Specification

### 4.1 Layout: 3-Column Analytical Grid

```
┌───────────────────────────────────────────────────────────────────┐
│ Top Navigation Bar (Command Bar)                                  │
│ [BR logo] Ba Reng? v1.0.0 | Live Feed | Entities | Constituencies │
│                              | Search ⌘K | [+ New Query]          │
├───────────────────────────────────────────────────────────────────┤
│ System Status Bar                                                  │
│ ● CRAWLER_ACTIVE | SOURCE: botswanaspeaks | LAST_RUN: 2026-...   │
│   DOCS_PARSED: 14 | ENTITIES_UNRESOLVED: 2                       │
├──────────┬────────────────────────────────────┬───────────────────┤
│ Filters  │   Live Record Stream               │ Participation     │
│          │                                    │ Index             │
│ Type     │ Timestamp | Entity | Type | Subject│ 01 Duma Boko  142 │
│ Party    │ ─────────────────────────────────── │ 02 Mmolotsi  118 │
│ Date     │ 14:02 | Thabologo    | ORAL_Q | ...│ 03 Kablay    95  │
│ Ministry │ 11:45 | Kapinga      | MOTION | ...│                   │
│          │ 09:15 | Duma Boko    | BILL_2ND| ..│ Constraint        │
│ Top      │ 16:30 | Mmolotsi     | ORAL_Q | ...│ ⚠ No attendance   │
│ Ministries│                                   │   data available   │
│          │                                    │                   │
│          │                                    │ Unresolved        │
│          │                                    │ Entities          │
│          │                                    │ "Mr T.Furniture"  │
│ Width: 2 │           Width: 7                 │ Width: 3          │
├──────────┴────────────────────────────────────┴───────────────────┤
│ Footer: Methodology | About | Source: Parliament of Botswana      │
└───────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Inventory

| Component | Based on | Description |
|---|---|---|
| `TopNav` | Palantir unified header | Minimal, versioned, ⌘K search |
| `SystemStatusBar` | Palantir terminal strip | Mono text, live pipeline health |
| `FilterPanel` | Blueprint `Select` + `DateRangeInput` | Collapsible, dense form controls |
| `RecordStream` | Blueprint `Table2` | Virtualized log, resizable columns, sortable |
| `ParticipationIndex` | Custom (thin bars) | 2px progress bars, mono rank |
| `ConstraintBlock` | Custom (amber) | Persistent structural UI, not popup |
| `UnresolvedEntities` | Custom (tag list) | Links to review queue |
| `MPProfile` | Blueprint `Card` + `Tabs` | Timeline, stats, source links |
| `ConstituencySearch` | Blueprint `Select` | Autocomplete, map to MP |
| `MPCompare` | Blueprint `Table2` side-by-side | Head-to-head |
| `BillTracker` | Blueprint `Timeline` | Stage progression |
| `ExportButton` | Blueprint `Button` | CSV/PDF per view |

### 4.3 Design Tokens

```css
/* Canvas & Surfaces */
--bg-canvas: #0B0E14;
--bg-surface: #11151C;
--bg-elevated: #161B24;

/* Borders — all 1px, never 2px+ */
--border-subtle: #1F242E;
--border-default: #2A313D;

/* Text — BP7-style scale */
--text-primary: #E4E8EE;
--text-secondary: #8B95A4;
--text-tertiary: #5A6473;

/* Functional Color — never decorative */
--accent-blue: #2D7FF9;
--accent-amber: #F5A623;
--accent-green: #16A34A;
--accent-red: #EF4444;

/* Typography — Inter + JetBrains Mono */
--font-ui: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', 'SF Mono', monospace;

/* Elevation — Blueprint BP7 box-shadow tokens */
--shadow-elevation-low: 0 1px 3px rgba(0,0,0,0.4);
--shadow-elevation-medium: 0 4px 12px rgba(0,0,0,0.5);

/* Radius — always 0 */
--radius: 0;
```

### 4.4 Token Role Discipline

- `--accent-blue`: primary data metrics, links, active filters, interactive tags
- `--accent-amber`: warnings, constraints, unresolved entities, methodology caveats
- `--accent-green`: system health (CRAWLER_ACTIVE, status dots)
- `--accent-red`: destructive actions only (never decorative)
- `--font-mono`: ALL timestamps, constituency codes, party codes, IDs, contribution types, tags, data values in tables, rank numbers
- `--font-ui`: everything else (names, subjects, descriptions)

---

## 5. Key Implementation Decisions

### 5.1 Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Crawl/Parser | Python 3.12 + `requests` + `pdfplumber` + `PyMuPDF` + `re` + `lingua-py` | PDF text extraction, regex splitting, language detection |
| Offline NLP | `spaCy` (`en_core_web_sm`) + custom `EntityRuler` | **Zero-LLM** entity extraction (locations, money, government entities) + Botswana gazetteer rules |
| Entity Resolution | Python (custom, no ML) | Constituency normalization + fuzzy surname match |
| Store | SQLite (single file) | Zero ops, git-versionable, SQL queryable |
| API | FastAPI | Async, auto-docs, lightweight |
| Frontend | React 19 + Vite + Blueprint.js (v5) | Data-dense Palantir-style interface |
| CSS | Tailwind CSS (utility) + Blueprint tokens | BP7 design tokens as CSS custom properties |
| Deploy | GitHub Actions → GitHub Pages / Vercel | Free tier, daily rebuild |
| Social | Python script + review queue | Never auto-post |

### 5.2 Why Blueprint.js Instead of shadcn/Radix

Blueprint is the component library that powers Palantir Foundry and AIP. It is:
- Built for data-dense desktop interfaces (our exact use case)
- Has `Table2` — a virtualized, resizable, sortable table with copy-to-clipboard
- Has `Select`, `MultiSelect`, `Suggest` — for filter controls
- Native dark mode via BP7 design tokens (CSS custom properties)
- Intent system (primary/success/warning/danger) maps directly to our color role system
- Not mobile-first (acceptable: this is a data dashboard, not a social app)

### 5.3 Crawl Logic

```python
def crawl_botswanaspeaks():
    # 1. Fetch listing page
    # 2. For each article, check raw_text_hash against documents table
    # 3. Skip if hash matches (unchanged)
    # 4. Download new/modified PDFs
    # 5. Return list of {source_url, pdf_url, title, published_date}
    # 6. Persist to crawl_runs with status=RUNNING
    #    On success: status=SUCCESS, new_documents=n
    #    On failure: status=FAILED, errors=n
```

The hash cache is critical. Botswana Speaks listing page may return full history. Without dedup, every run would re-parse every PDF.

### 5.4 Entity Resolution Logic

```python
def resolve_mp(raw_name: str, constituency_raw: str) -> tuple[mp_id | None, status]:
    """Returns (mp_id or None, 'RESOLVED' | 'UNRESOLVED')"""
    
    # Normalize constituency
    constituency_norm = normalize(constituency_raw)
    # lowercase, strip punctuation, collapse whitespace
    
    # 1. Exact constituency match
    if mp := mps_by_constituency.get(constituency_norm):
        return (mp.id, 'RESOLVED')
    
    # 2. Constituency fuzzy match (typo correction)
    if matches := fuzzy_match_constituency(constituency_norm):
        return (matches[0].mp_id, 'RESOLVED')
    
    # 3. Surname match for specially-elected
    surname = extract_surname(raw_name)
    if mp := mps_by_surname.get(surname):
        return (mp.id, 'RESOLVED')
    
    # 4. No match — store in review queue
    return (None, 'UNRESOLVED')
```

### 5.5 Participation Index Formula

```python
def participation_index(mp_id: int) -> dict:
    """Returns weighted score + breakdown. Explicitly a proxy metric."""
    
    contributions = query("""
        SELECT contribution_type, COUNT(*) as count
        FROM contributions
        WHERE mp_id = ? AND date >= ?
        GROUP BY contribution_type
    """, mp_id, session_start)
    
    weights = {
        'oral_question': 1.0,
        'motion': 1.5,        # motions require more initiative
        'bill_reading': 1.0,
        'committee_of_supply': 1.5,
        'ministerial_q': 1.0,
    }
    
    total = sum(c.count * weights.get(c.type, 1.0) for c in contributions)
    breakdown = {c.type: c.count for c in contributions}
    
    return {
        'score': total,
        'breakdown': breakdown,
        'is_proxy': True,
        'caveat': 'Based on recorded contributions only. Not attendance data.',
    }
```

The `is_proxy` flag controls UI rendering — any view displaying the index must show the caveat. This is enforced in the component, not left to the developer.

### 5.6 Multilingual & Code-Switching Processing Engine

Because the Botswana Hansard mixes English and Setswana within the same speech turn, a bilingual detection and normalization layer runs before entity extraction.

```python
import re
import spacy
from spacy.pipeline import EntityRuler
from lingua import Language, LanguageDetectorBuilder

# 1. Fast Language Detector for English / Setswana Code-Switching
languages = [Language.ENGLISH, Language.TSWANA]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

def detect_language(text: str) -> str:
    """Classifies speech turn as 'en', 'tn', or 'mixed'."""
    confidence_values = detector.compute_language_confidence_values(text)
    scores = {val.language: val.value for val in confidence_values}

    en_score = scores.get(Language.ENGLISH, 0.0)
    tn_score = scores.get(Language.TSWANA, 0.0)

    if abs(en_score - tn_score) < 0.2 and (en_score > 0.3 and tn_score > 0.3):
        return "mixed"
    return "tn" if tn_score > en_score else "en"

# 2. Custom spaCy Pipeline with Botswana Gazetteer Rules
nlp = spacy.load("en_core_web_sm")
ruler = nlp.add_pipe("entity_ruler", before="ner")

# Load Botswana Gazetteers (Villages, Constituencies, Ministries)
patterns = [
    {"label": "GPE", "pattern": "Mohembo"},
    {"label": "GPE", "pattern": "Okavango"},
    {"label": "GPE", "pattern": "Tsabong"},
    {"label": "GPE", "pattern": "Mmopane-Metsimotlhabe"},
    {"label": "ORG", "pattern": "DPSM"},
    {"label": "ORG", "pattern": "Public Service Commission"},
    {"label": "ORG", "pattern": "Lephata la Temothuo"},  # Ministry of Agriculture in Setswana
]
ruler.add_patterns(patterns)

# 3. Honorific Normalizer for Entity Resolution & FTS
BOTSWANA_HONORIFICS = r"\b(Motlotlegi|Rre|Mma|Kgosi|Tona|Honourable|Hon|Mr|Mrs|Ms|Dr)\b"

def normalize_speaker_and_text(raw_text: str) -> str:
    """Strips honorifics to allow accurate matching against standard MP names."""
    return re.sub(BOTSWANA_HONORIFICS, "", raw_text, flags=re.IGNORECASE).strip()
```

### 5.7 Hansard Free-Text Parsing & Regex Engine Details

Because parliamentary Hansard transcripts adhere to official formatting rules, they can be processed deterministically:

**Hansard Session Header Patterns:**
- Hansard Number: `r"HANSARD NO:\s*(\d+)"`
- Session Date: `r"(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY)\s+(\d{1,2}(?:ST|ND|RD|TH)?\s+[A-Z]+\s*,?\s*\d{4})"`
- Assembly Time: `r"THE ASSEMBLY met at\s*(\d{1,2}:\d{2}\s*[a-z\.]*)"`

**Speaker Turn Regex Patterns:**
- Speaker with constituency: `r"^([A-Z\s\.]+)\s*\(([^)]+)\):\s*"` (e.g., `MR K. K. KAPINGA (OKAVANGO WEST):`)
- Speaker with Portfolio: `r"^([A-Z\s]+)\s*\(([A-Z\s\.]+)\):"` (e.g., `MINISTER OF ENVIRONMENT AND TOURISM (MR MMOLOTSI):`)
- Abbreviated Speaker Turn: `r"^([A-Z\s\.]+):"` (e.g., `MR SPEAKER:`, `MR PULE:`, `DR DIKOLOTI:`)

**Turn Type Qualifiers:**
- Supplementary Question: Checks if text begins with `Supplementary.` or `Further Supplementary.`.
- Point of Order / Procedure: Checks if turn begins with `On a point of procedure.`.
- Deferral: Detects `Later Date.`.

**Procedural Actions Regex:**
- Parenthetical events: `r"\(\.\.\.(.*?)\dots\)"` (captures `...(Applause!)...`, `...(Laughter!)...`).

**Entity Extraction Logic (`nlp_extract.py`):**
```python
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_speech_entities(speech_text: str) -> dict:
    doc = nlp(speech_text)
    entities = {"locations": [], "money": [], "orgs": []}

    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            entities["locations"].append(ent.text)
        elif ent.label_ == "MONEY":
            entities["money"].append(ent.text)
        elif ent.label_ == "ORG":
            entities["orgs"].append(ent.text)

    return {k: list(set(v)) for k, v in entities.items()}
```

---

## 6. Anti-Slop Pass

| Check | Status |
|---|---|
| Dark palette is cold slate (`#0B0E14`), not warm cream/terracotta | ✅ |
| No `rounded-2xl` cards with drop shadows | ✅ — radius=0, hairline borders |
| No decorative serif/italic word swaps in headlines | ✅ — Inter only, no serif |
| No generic glassmorphism | ✅ |
| Color is functional, not decorative | ✅ — blue=data, amber=warning, green=health |
| No animated hero section with gradient CTA | ✅ — static status bar instead |
| No stock photography of "diverse team collaborating" | ✅ — no imagery at all |
| Every major design choice traces to a reference | ✅ — Palantir, Blueprint, BungeMeter, civic.ng |
| No attendance data framed as attendance | ✅ — "Participation Index" labeled proxy |
| No "most active" / "least active" language | ✅ — "most/least recorded contributions" |
| Methodology constraint is structural UI, not a popup | ✅ — always-visible sidebar block |
| Unresolved entities exposed transparently | ✅ — not hidden or silently guessed |

---

## 7. Narrative-First Design

### 7.1 Principle

Data must tell a story. Every screen must answer a question the user is actually asking:

| User Question | Screen | Story Told |
|---|---|---|
| "What happened this week?" | This Week in Parliament (home) | Top story, weekly timeline, hot topics, who was active |
| "Is my MP doing their job?" | MP Profile | Contribution breakdown, ministry focus, session narrative |
| "How do two MPs compare?" | MP Compare | Not just numbers — a comparison *story* that explains the gap |
| "What's Parliament working on?" | Bill Tracker | Legislative progress as a journey, not a status list |
| "Who is shaping the session?" | Participation Index | Ranked by contribution, with trend and caveat inline |

### 7.2 Home Page — The Narrative Dashboard

The default landing page is no longer a raw feed. It is a **weekly parliamentary digest**:

1. **Week at a Glance** — 4 stat cards (sitting days, contributions, active MPs, most-addressed ministry)
2. **Top Story This Week** — single most notable contribution, contextualized (who, what ministry, why it matters)
3. **This Week's Timeline** — day-by-day breakdown of what happened
4. **Who Was Active** — top 5 MPs this week with contribution counts
5. **By the Numbers** — quick stats table (questions, motions, bills, ministries)
6. **Hot Topics** — thematic grouping of contributions (e.g., "Finance & Budget", "Infrastructure")
7. **Recent Contributions** — compact scrollable list linking to raw feed
8. **Quick Actions** — Find MP, Compare MPs, Browse Bills

The raw **Live Record Stream** (Screen 2) is preserved for power users who need unfiltered access.

### 7.3 MP Profile — Session Focus Narrative

Each MP profile includes a **"Session Focus"** block (amber/blue-bordered) that answers: *"What does this MP care about?"* — derived from ministry focus breakdown, contribution type ratios, and trend over time. This transforms a stats page into a biographical tool.

### 7.4 Compare — Comparison Story

The compare screen opens with a prose comparison that highlights the *meaningful* difference between two MPs — not just which numbers are bigger, but what the gap implies about different parliamentary strategies (e.g., "Boko's motions suggest legislative initiative; Furniture's oral questions indicate oversight focus").

---

## 8. Administration Dashboard & RBAC

### 8.1 Architecture

Admin is **integrated under `/admin/*`** in the same React app, route-guarded by React Router. JWT auth with httpOnly cookie.

```
POST /api/v1/auth/login          → JWT token
POST /api/v1/auth/logout         → invalidate token
GET  /api/v1/auth/me             → current user + role

GET    /api/v1/admin/users          → [User]              Admin
POST   /api/v1/admin/users          → create User         Admin
PATCH  /api/v1/admin/users/{id}     → update/deactivate   Admin

GET    /api/v1/admin/entities       → entity_review_queue  Editor+
PATCH  /api/v1/admin/entities/{id}  → resolve/ignore      Editor+

POST   /api/v1/admin/crawl/trigger  → start crawl         Admin
GET    /api/v1/admin/crawl/runs     → crawl history       Admin

GET    /api/v1/admin/health         → system status       Viewer+
PATCH  /api/v1/admin/contributions/{id} → flag/review     Editor+
```

### 8.2 Data Model (New Tables)

```
users
├── id (pk)
├── email (unique)
├── password_hash (bcrypt via passlib)
├── display_name
├── role: admin | editor | viewer
├── is_active (boolean)
├── created_at
└── last_login_at (nullable)

sessions
├── id (pk)
├── user_id (fk → users)
├── token (unique JWT)
├── expires_at
└── created_at
```

### 8.3 Admin Screens

| Route | Component | Access | Purpose |
|---|---|---|---|
| `/admin` | AdminDashboard | Viewer+ | Pipeline health, data quality stats, recent crawl runs, audit log |
| `/admin/entities` | EntityReviewQueue | Editor+ | Resolve unmatched names with suggestion engine |
| `/admin/users` | UserManagement | Admin only | CRUD table, invite form, role assignment |
| `/admin/crawls` | CrawlLog | Admin only | Run history, error details, manual trigger |
| `/admin/contributions` | ContributionReview | Editor+ | Flag/review contributions for accuracy |

### 8.4 Auth Flow

```
Login Page (/login) → POST /api/v1/auth/login → JWT in httpOnly cookie
→ AuthContext provides { user, role } to React
→ ProtectedRoute checks role before rendering /admin/*
→ API client attaches Authorization: Bearer via interceptor
→ 401 response → redirect to /login
```

### 8.5 Stack

| Layer | Choice |
|---|---|
| Auth tokens | `python-jose` JWT, 24h expiry |
| Password hashing | `passlib` + `bcrypt` |
| API middleware | FastAPI dependency injection: `get_current_user()`, `require_role(roles)` |
| Frontend auth | React context + ProtectedRoute component |
| Session store | `sessions` table in SQLite (no Redis needed at this scale) |

---

## 9. Merged Mockup

The file `ba-reng-combined.html` replaces both previous mockups. It contains 11 screens:

| # | Screen | Type | Description |
|---|---|---|---|
| 01 | This Week in Parliament | Public | Narrative dashboard (default home) |
| 02 | Live Record Stream | Public | Raw filtered feed |
| 03 | Find My MP | Public | Constituency search |
| 04 | MP Profile | Public | Stats + session focus narrative |
| 05 | MP Compare | Public | Side-by-side with comparison story |
| 06 | Participation Index | Public | Leaderboard with caveat |
| 07 | Bill Tracker | Public | Legislative progress |
| 08 | Search | Public | Full-text search |
| 09 | Admin Dashboard | Admin | Pipeline health, data quality, crawl log |
| 10 | Entity Review Queue | Admin | Resolve unmatched names |
| 11 | User Management | Admin | CRUD users + RBAC matrix |

All screens use the Palantir token system. The file is self-contained (no build step).

---

## 10. Sources

- Palantir Foundry Workshop layout docs — palantir.com/docs/foundry/workshop/
- Palantir Blueprint.js — blueprintjs.com, github.com/palantir/blueprint (BP7 tokens, July 2026)
- BungeMeter/Mzalendo — bungemeter.mzalendo.com (June 2026)
- ParliMeter — parlimeter.org.za (2025-2026)
- civic.ng — civic.ng (live)
- Scorecard Nigeria — scorecardnigeria.com (live)
- CPU Uganda — cpuganda.com (live)
- BungeWatch — github.com/declerke/Bunge-Watch (April 2026)
- Legis360 — legis360.org (2025-2026)
- Botswana Speaks — botswanaspeaks.gov.bw (Parliament of Botswana)
