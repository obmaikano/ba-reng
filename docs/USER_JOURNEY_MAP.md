# Ba Reng? — User Journey Map

*11 screens, 3 persona paths, every click traced*

---

## Conventions

```
CLICK [element] → [destination]
INPUT [field] → action
ICON [icon name] → action
MODAL [name] → contents
```

Screen layout modes:
- **Full-width**: Screen 01 (narrative dashboard, no sidebars)
- **3-column**: Screens 02–08 (left sidebar data filters | feed col-7 | right panel index)
- **Admin mode**: Screens 09–11 (left sidebar admin nav | content col-7 | right panel health)

---

## Persona 1: Citizen (entry point: Find My MP or search)

### 1A — Find My MP (Screen 03)

```
ENTRY: TopNav "03 Find MP" click → Screen 03 loads in 3-column layout
  Sidebar: data filters (hidden by default)
  Right panel: Participation Index + Methodology constraint

INPUT [Search input] → type constituency name (autocomplete)
CLICK [Search button] → results appear below
CLICK [Suggested constituency "Gaborone"] → pre-fills search
CLICK [Suggested constituency "Francistown"] → pre-fills search
CLICK [Browse all 57 constituencies] → directory list expands

MATCH FOUND:
  CLICK [Result card: Thabologo Furniture, Tati East] → Screen 04 (MP Profile)
  CLICK [Result card: Shakkie Tlou, Tati East] → Screen 04 (MP Profile)

NO MATCH:
  CLICK [browse all constituencies] → directory list expanded
  CLICK [Constituency item "Tati East"] → filters list

SIDEBAR INTERACTIONS (any screen):
  CLICK [Reset] → clears all filters
  SELECT [Type dropdown] → filter feed by contribution type
  SELECT [Party dropdown] → filter by party
  SELECT [Ministry dropdown] → filter by ministry
  INPUT [Date From / Date To] → date range filter
  INPUT [Constituency] → constituency filter

RIGHT PANEL INTERACTIONS (any data screen):
  CLICK [View full leaderboard →] → Screen 06
  CLICK [VIEW_METHODOLOGY →] → methodology info
  CLICK [REVIEW (unresolved entities)] → Screen 10 (if admin/editor)

TOPNAV (persistent, any screen):
  CLICK [01 Week] → Screen 01
  CLICK [02 Feed] → Screen 02
  CLICK [03 Find MP] → Screen 03
  CLICK [04 Profile] → Screen 04
  CLICK [05 Compare] → Screen 05
  CLICK [06 Rank] → Screen 06
  CLICK [07 Bills] → Screen 07
  CLICK [08 Search] → Screen 08
  CLICK [09 Admin] → Screen 09 (if authenticated)
  CLICK [10 Entities] → Screen 10 (if authenticated)
  CLICK [11 Users] → Screen 11 (if authenticated)
```

### 1B — MP Profile (Screen 04)

```
ENTRY: From Screen 03 result card click, or any MP name click across platform

HEADER: photo placeholder, name, constituency, party, role
  CLICK [Compare button] → Screen 05, pre-selected with this MP
  CLICK [Share button] → share dialog

TABS:
  CLICK [Tab: Timeline] → chronological contribution list (default)
  CLICK [Tab: By Type] → breakdown chart by contribution type
  CLICK [Tab: Ministries] → breakdown by ministry addressed
  CLICK [Tab: Compare] → Screen 05 pre-selected

CONTRIBUTION LIST:
  CLICK [external-link icon] → source PDF in new tab
  CLICK [contribution row] → expanded detail inline

FOOTER ACTIONS:
  CLICK [What does this mean?] → methodology caveat explanation
  CLICK [Load more] → paginate older contributions
  CLICK [Export CSV] → download profile data
  CLICK [View source docs] → source document list
```

### 1C — Compare MPs (Screen 05)

```
ENTRY: From Screen 04 "Compare" button, TopNav, or Screen 01 quick action

SELECT [MP A dropdown] → choose first MP
SELECT [MP B dropdown] → choose second MP

AUTO: Comparison story prose generates below
AUTO: Side-by-side stat cards render (total contributions, breakdown by type)
AUTO: Bar chart comparison renders

CLICK [Download as PDF] → exports comparison
```

---

## Persona 2: Power User (lives in the feed)

### 2A — This Week in Parliament (Screen 01, HOME)

```
ENTRY: Page load or TopNav "01 Week"

WEEK AT A GLANCE (4 stat cards):
  Sitting days this week
  Contributions recorded
  Active MPs
  Most-addressed ministry
  → All stat cards are informational (no click)

TOP STORY:
  CLICK [Read full Q&A →] → expands question/answer text inline
  Story card has blue left border → clickable

THIS WEEK'S TIMELINE (day-by-day):
  Each day: list of events/contributions
  CLICK [day event row] → Screen 02 filtered to that date

WHO WAS ACTIVE (top 5 MPs):
  CLICK [Boko / Furniture / Mmolotsi / Kapinga / Kablay row] → Screen 04
  CLICK [View full leaderboard →] → Screen 06

BY THE NUMBERS:
  Table: Questions | Motions | Bills | Ministries addressed
  → Informational, no click actions

HOT TOPICS:
  Thematic groupings
  CLICK [topic card] → Screen 02 filtered by topic
  CLICK [View full feed →] → Screen 02

RECENT CONTRIBUTIONS (compact scrollable):
  CLICK [file-text icon] → source PDF
  CLICK [contribution line] → Screen 02 scrolled to that item

QUICK ACTIONS:
  CLICK [Find Your MP] → Screen 03
  CLICK [Compare MPs] → Screen 05
  CLICK [Browse Bills] → Screen 07

METHODOLOGY / LINKS:
  CLICK [VIEW_METHODOLOGY →] → methodology info
  CLICK [View full leaderboard →] → Screen 06
  CLICK [Review] → Screen 10 (if authenticated)
```

### 2B — Live Record Stream (Screen 02)

```
ENTRY: TopNav "02 Feed"

TOOLBAR:
  CLICK [Filter] → toggles filter panel visibility
  CLICK [CSV] → exports current view

TABLE (virtualized, sortable):
  Columns: Timestamp | Entity | Type | Subject
  CLICK [column header] → sort asc/desc
  CLICK [feed row] → expanded contribution detail (inline or modal)
  CLICK [file-text icon on row hover] → source PDF

PAGINATION:
  CLICK [Load more →] → next page

SIDEBAR (left): data filters (see Persona 1 sidebar)
RIGHT PANEL: Participation Index + constraints
```

### 2C — Search (Screen 08)

```
ENTRY: TopNav "08 Search" or ⌘K keyboard shortcut

INPUT [Search input] → type query (e.g. "Mohembo Bridge")
CLICK [Search button] → execute search

FILTERS:
  SELECT [Type filter] → narrow by contribution type
  SELECT [Party filter] → narrow by party
  SELECT [Ministry filter] → narrow by ministry
  CLICK [Clear] → reset all filters

RESULTS (grouped by relevance):
  CLICK [result row] → contribution detail
  CLICK [chevron-right icon] → contribution detail
```

---

## Persona 3: Analyst/Researcher

### 3A — Participation Index (Screen 06)

```
ENTRY: TopNav "06 Rank" or leaderboard link from Screen 01/02

TOOLBAR:
  CLICK [CSV] → export leaderboard data
  SELECT [Party filter] → filter by party

LEADERBOARD TABLE:
  Rank | MP | Party | Score | Breakdown
  CLICK [MP row] → Screen 04

CAVEAT: "Proxy metric" label always visible (amber) — not a dismissible popup
```

### 3B — Bill Tracker (Screen 07)

```
ENTRY: TopNav "07 Bills" or "Browse Bills" from Screen 01

TOOLBAR:
  SELECT [Stage filter] → filter by legislative stage

BILL LIST:
  CLICK [bill card] → expanded bill detail with stage timeline
  Stage timeline: Introduced → 1st Reading → 2nd Reading → Committee → 3rd Reading → Passed
  CLICK [View debate →] → Screen 02 filtered to that bill
```

---

## Persona 4: Admin/Editor

### 4A — Admin Dashboard (Screen 09)

```
ENTRY: TopNav "09 Admin"

STAT CARDS:
  Pipeline health (green/amber/red)
  Data quality stats
  System status

ACTIONS:
  CLICK [Trigger Crawl] → initiates manual crawl (Admin only)
  CLICK [Export] → export admin data

QUICK LINKS:
  CLICK [Manage users] → Screen 11
  CLICK [Entity review queue] → Screen 10
  CLICK [Crawl log] → detailed crawl run history
  CLICK [Flagged contributions] → flagged contributions list

CRAWL RUNS TABLE:
  CLICK [View all runs →] → full crawl log page

SIDEBAR (left): admin navigation
  CLICK [Dashboard] → Screen 09
  CLICK [Entity Review (2)] → Screen 10
  CLICK [User Management] → Screen 11
  CLICK [Crawl Log] → crawl log detail
  CLICK [Flagged Contributions] → flagged contributions

RIGHT PANEL (admin): system health
  CLICK [Review (2 unresolved)] → Screen 10
```

### 4B — Entity Review Queue (Screen 10)

```
ENTRY: TopNav "10 Entities" or admin sidebar link

TOOLBAR:
  CLICK [Refresh] → refresh queue

ENTITY TABLE:
  Each row: raw name | source document | suggested MP match

  FOR EACH ENTITY:
    SELECT [Resolve dropdown] → choose matching MP from roster
    CLICK [Resolve button] → confirms match, updates contribution
    CLICK [Skip button] → marks as IGNORED, removes from queue
```

### 4C — User Management (Screen 11, Admin only)

```
ENTRY: TopNav "11 Users" or admin dashboard link

USER TABLE:
  Email | Name | Role | Status | Last Login | Actions
  CLICK [Edit (user row)] → inline edit form
    → Change role dropdown
    → Deactivate/reactivate toggle
    → Save / Cancel

TOOLBAR:
  CLICK [Add User] → reveals invite form below table

INVITE FORM:
  INPUT [Email] → user email address
  INPUT [Display Name] → full name
  SELECT [Role] → Admin / Editor / Viewer
  CLICK [Send Invitation] → sends invite email, adds user row
```

---

## Global UI Behaviors

### TopNav (persistent across all screens)

```
Left section:
  [BR logo] [Ba Reng? v1.0.0] [NARRATIVE_DASHBOARD tag]

Public nav buttons:
  [01 Week] [02 Feed] [03 Find MP] [04 Profile] [05 Compare]
  [06 Rank] [07 Bills] [08 Search]

Admin nav buttons (visible only when authenticated):
  [09 Admin] [10 Entities] [11 Users]

Right section:
  [Search ⌘K] → opens search (Screen 08)
  [+ New Query] → opens query builder
```

### SystemStatusBar (below TopNav, persistent)

```
[● CRAWLER_ACTIVE] [SOURCE: botswanaspeaks] [LAST_RUN: 2026-...]
[DOCS_PARSED: 14] [ENTITIES_UNRESOLVED: 2] [⚠ PROXY_METRIC]
  → All indicators are informational, no click actions
```

### Layout Transitions

```
Screen 01 (full-width):
  │ TopNav │ SystemStatusBar │
  │                                                           │
  │                  THIS WEEK IN PARLIAMENT                  │
  │           (full-width narrative dashboard)                │
  │                                                           │
  │                         Footer                            │

Screens 02-11 (3-column):
  │ TopNav │ SystemStatusBar │
  ├──────────┬────────────────────────────┬───────────────────┤
  │  Sidebar │     Content (col-7)        │   Right Panel     │
  │  (col-2) │     (feed/admin view)      │   (col-3)         │
  │          │                            │                   │
  │ Filters  │  Live Record Stream         │ Participation     │
  │ or       │  or MP Profile             │ Index             │
  │ Admin Nav│  or Admin Screen            │ or                │
  │          │                            │ System Health     │
  └──────────┴────────────────────────────┴───────────────────┘
```

Sidebar swaps: Screens 02-08 → data filters. Screens 09-11 → admin nav.
Right panel swaps: Screens 02-08 → Participation Index. Screens 09-11 → System Health.

### Transitions

```
CLICK [nav-btn] → switchScreen(target):
  1. Current feed-view gets class "anim-out" (150ms fade+translate)
  2. Target feed-view gets class "anim-in" (250ms fade+translate)
  3. Sidebar content swaps (data ↔ admin)
  4. Right panel content swaps (index ↔ health)
```

---

## Cross-Screen Navigation Index

| From | Element | To |
|---|---|---|
| 01 | MP row (Who Was Active) | 04 (MP Profile) |
| 01 | View full leaderboard | 06 (Participation Index) |
| 01 | Compare MPs | 05 (Compare) |
| 01 | View full feed | 02 (Live Record Stream) |
| 01 | Find Your MP | 03 (Find My MP) |
| 01 | Browse Bills | 07 (Bill Tracker) |
| 01 | Review | 10 (Entity Review Queue) |
| 02 | MP name in feed row | 04 (MP Profile) |
| 03 | Result card | 04 (MP Profile) |
| 04 | Compare button | 05 (Compare, pre-filled) |
| 04 | Tab: Compare | 05 (Compare, pre-filled) |
| 06 | MP row | 04 (MP Profile) |
| 07 | View debate | 02 (filtered) |
| 09 | Manage users | 11 (User Management) |
| 09 | Entity review queue | 10 (Entity Review Queue) |
| All | TopNav buttons | Any screen |
| All | Right panel: View full leaderboard | 06 |
| All | Right panel: REVIEW | 10 |

---

## Interaction Count Summary

| Screen | Clickable Elements | Input Fields | Total Interactive |
|---|---|---|---|
| 01 — This Week | 20 | 0 | 20 |
| 02 — Live Feed | 13 | 0 | 13 |
| 03 — Find My MP | 17 | 1 | 18 |
| 04 — MP Profile | 15 | 0 | 15 |
| 05 — Compare | 4 | 0 | 4 |
| 06 — Participation Index | 9 | 1 | 10 |
| 07 — Bill Tracker | 8 | 1 | 9 |
| 08 — Search | 9 | 1 | 10 |
| 09 — Admin Dashboard | 12 | 0 | 12 |
| 10 — Entity Review | 9 | 2 | 11 |
| 11 — User Management | 10 | 3 | 13 |
| Global (TopNav + StatusBar) | 11 | 0 | 11 |
| **Total** | **137** | **9** | **146** |

---

## Auth-Gated Elements

| Element | Minimum Role | Screen |
|---|---|---|
| 09 Admin nav button | Viewer+ | Persistent TopNav |
| 10 Entities nav button | Editor+ | Persistent TopNav |
| 11 Users nav button | Admin | Persistent TopNav |
| Trigger Crawl | Admin | 09 |
| Manage Users link | Admin | 09 |
| Crawl Log | Admin | 09 |
| Resolve/Skip entity | Editor+ | 10 |
| Add/Edit/Deactivate User | Admin | 11 |
| Sidebar admin nav | Viewer+ | 09-11 |
| Right panel system health | Viewer+ | 09-11 |
