# CLAUDE.md — flightview-api (SkyDial Pi back-end)

## What this repo is

`flightview-api` is the **Raspberry Pi back-end service** for **SkyDial** — a window-sill ADS-B
aircraft HUD. This service ingests ADS-B data, calculates distance/bearing/elevation, filters and
scores aircraft against window profiles, enriches them, and serves a tiny JSON API over Wi-Fi to an
**M5Dial** (and, in future, a **Cardputer**) presentation layer. The Dial firmware lives outside
this repo. See `PRD.md` for the full product definition.

---

## My Working Practices

> These are the standing working practices for this project. Adhere to them as if they were system
> instructions. They describe a product-development operating method built around a canon of living
> documents: **PRD → STORYMAP → ARCHITECTURE → EPICS**, sliced the Jeff Patton / Mike Cohn / INVEST
> way. The PRD and STORYMAP master templates are inlined in the appendices — no external file
> dependencies. Where this names a "skill", that is an optional accelerator: **if the skill exists in
> this environment, use it; if not, follow the inline guidance instead.**

### Who I am / how to work with me

I'm a Head of Product — highly technical and architecture-aware, but not a software engineer. Treat
me like a stream-aligned product-dev team I'm pair-driving with: I give goals and broad direction
("make it so", "carry on") and expect you to fill in the details and make judgement calls. Be
technical, specific, and succinct. Skip apology loops. When you screw up, fix it — don't write an
essay about it. Suggest improvements at appropriate junctures; I welcome a high-calibre colleague
who challenges the approach, not a doormat.

The personas in the PRD are real and there's real operational/commercial benefit behind the work.
Keep a continual drive to deliver customer value and to surprise and delight end users.

#### Cadence

- **Stop between epics for manual eyeball QA** — unless explicitly told "in parallel" or "as a
  batch". When sequencing through epics, halt after each with a clear "what to eyeball" handoff.
- **Drive, don't ask.** When the path is clear, just do it. Ask only on genuine ambiguity, and when
  you ask, make it cheap — one short question with a recommendation.
- **Brief is good — silent is not.** State what you're doing in one sentence, narrate at key
  moments, summarise at the end. No padding, no recaps of recaps.
- **Multi-message bursts mean prioritise + sequence.** Work through several asks in the order given.
- **Set expectations on long-running work.** Estimate how long a build/compile/process will take and
  say so as you kick it off.

#### Trust signals

- "I'm loving it" / "perfect" / "exactly" = on the right track, keep going.
- "make it so" / "go for it" / "carry on" = green light, no further confirmation needed.
- "stop doing X" / "no not that" = correction; treat as a durable preference going forward.
- Silence after a long handoff = I've gone to do something else. The work continues.

---

### The document canon

These are the blessed living documents. Create and maintain them **automatically** as part of the
standard process — that is not "rivalling" the canon, it *is* the canon. Only a genuinely net-new
*type* of doc outside this list needs justification before you create it.

| Doc | Purpose |
| --- | --- |
| **PRD.md** | Canonical record of purpose, functionality, personas, requirements, future path. Written to the master template (Appendix A). |
| **STORYMAP.md** | Jeff Patton story map — the user-journey view of the PRD Requirements table. Drives the EPICS tiers. Template in Appendix B. |
| **ARCHITECTURE.md** | The architecture that supports both the end state and future states, allowing iteration without re-factoring. |
| **EPICS.md** | The plan: epics → stories, story-pointed, organised into MTP→MVP→MSP→MLP tiers derived from the STORYMAP release slices. Index/tracker table. |
| **EPIC-NN.md** | When the backlog grows past ~12 epics, give each its own detail file (description, value, AC, stories); the EPICS.md index keeps a one-line teaser per epic. |
| **SNAGGING.md** | Prioritised, story-pointed list of bugs and issues. Small easy betterment fixes: just do them. |
| **VELOCITY.md** | (Optional) spend + velocity dashboard, generated — never hand-edit. See "Velocity" note below. |
| **DEPLOYMENT.md** | Deployment steps and any deviation from standard pipelines. |
| **NIGHTNIGHT.md** | Resume-from-here state when putting the project down for the night. Emptied once resumed. |
| **SCRATCHPAD.md** | Loose working notes. Keep it germane — don't let it fill with crap. |
| **README.md / CLAUDE.md** | Standard. Keep CLAUDE.md updated as you learn about the codebase. |

#### Planning flow (do these in order when starting a product)

1. **Discovery (upstream of the map, optional):** frame the problem before deciding what to build.
   Use `opportunity-solution-tree`, `jobs-to-be-done`, `problem-statement` skills if available;
   otherwise: state the desired outcome, branch into opportunities (customer problems), then
   candidate solutions, then the cheapest test that would validate each.

2. **PRD.md** — write/refresh to the master template in Appendix A. Preserve the section structure,
   ordering, the 8-column story-mapping Requirements/Out-of-Scope table, and the controlled-vocabulary
   lozenges:
   - **Importance (phase):** `ALPHA | BETA | GTM | Future`
   - **Persona involvement:** `SIGN-OFF | INFLUENCER | USER | DELIVERY | IN-LIFE SERVICE`
   Don't invent a different PRD layout.

3. **STORYMAP.md** — once the PRD Requirements table exists, lay it out as a Patton story map
   (Appendix B). A **backbone** of 3–5 sequential user **Activities** (user *behaviours* — never
   features or tech layers), each split into **Steps** then **Tasks**, with priority descending
   vertically. The PRD Requirements table and STORYMAP are **two views of one dataset** — the table's
   `Action`/`Step` columns are the map's Activities/Steps, and its `Importance` lozenges stay in sync
   with the map's release slices. Cut a **Walking Skeleton** (thinnest top-priority task across
   *every* activity — a complete end-to-end journey at its simplest), then **Release slices** (R1
   Walking Skeleton → R2 Enhanced → R3 Polish). Build left-to-right, top-to-bottom — thin slices
   across the whole backbone. Re-cut whenever scope shifts. (Skill: `user-story-mapping-workshop`, or
   `user-story-mapping` for a single pass.)

4. **ARCHITECTURE.md** — design an architecture that supports the end state and future states so we
   iterate towards it without re-factoring. Re-evaluate **before starting an epic and after finishing
   each one**: make subtle updates automatically; for a *major* architectural shift, tell me why
   you're proposing it, the impact, and the benefit. Keep it current at all times.

5. **EPICS.md** — once requirements, design and architecture exist, document epics that build to:
   - **MTP** (Minimum Testable Product) — early functional end-to-end
   - **MVP** (Minimum Viable Product) — demo-able
   - **MSP** (Minimum Sellable Product) — feature-complete, deliverable to paying users
   - **MLP** (Minimum Lovable Product) — bells, whistles, delight

   Derive the tiers **directly from the STORYMAP release slices**: **Walking Skeleton = MTP**, **R2 =
   MVP**, **R3 = MSP**, below-the-line ribs = **MLP**. Every tier is a **thin slice across the whole
   backbone**, never one activity built fully before the next (that's feature-complete waterfall — the
   cardinal sin). Re-evaluate before and after each epic, same rule as ARCHITECTURE. Epics and stories
   are story-pointed.

#### Slicing stories (INVEST / Patton / Cohn)

Slice each map Task into INVEST-sized stories. Skill: `epic-breakdown-advisor` (Humanizing Work
9-pattern flowchart). If unavailable, apply the method directly:

- **Validate INVEST-minus-Small first.** A good story is **I**ndependent, **N**egotiable,
  **V**aluable, **E**stimable, **S**mall, **T**estable. Check all *except* Small before splitting.
- **If a slice isn't *Valuable*, recombine rather than split.** Never ship a story that delivers no
  observable user value.
- **Always vertical slices** that deliver observable user value end-to-end — **never** horizontal
  front-end/back-end splits.
- Common split patterns: workflow steps · business-rule variations · happy path vs edge cases ·
  data-entry methods · simple-then-complex · defer performance · CRUD operations · break out a spike.

Write each story with the `user-story` skill if available; otherwise use **Mike Cohn** format plus
**Gherkin** acceptance criteria:

    As a <persona>, I want <capability>, so that <benefit>.

    Acceptance criteria:
      Given <context>
      When  <action>
      Then  <observable outcome>

Story-point at the story level. The STORYMAP slices become the EPICS tiers.

#### Velocity (optional)

If the project tracks spend/velocity: every commit is auto-attributed and bucketed by
conventional-commit type (`feat`/`fix`/`perf`/`refactor` = delivery; `docs`/`chore`/`test`/`ci` =
planning). Points are optional and human — add a `Points: N` trailer to a commit to feed the
forecast. `VELOCITY.md` is generated, never hand-edited. (This depends on project-specific tooling —
skip if it isn't set up.)

---

### Git discipline (atomic commits)

- **Commit after every story.** When a story is complete and leaves the build in a working state,
  make one atomic, conventional-commit-formatted commit for that story before starting the next. One
  story = one focused commit.
- **Never leave the repo in a broken state.** If a story is a breaking change that only makes sense
  once a following story lands, either (a) sequence work so each commit is coherent and non-breaking,
  or (b) hold the commit until the dependent stories complete and commit them together as one coherent
  unit. The committed state must always build/run.
- **Breaking-state commits need explicit approval** — the only time you may push a knowingly-broken
  state. Never assume it's OK.
- **Flag non-atomic cases up front** when planning epics/stories, so the dependency is visible before
  work starts.

#### Commit message convention

Conventional commits: `type(scope): description`

- **type** — `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, etc.
- **scope** — the affected app/component/area (e.g. `api`, `auth`, `ui`). Optional when repo-wide.
- **Never put a ticket number as the scope.** The scope says *what* changed, not *why*.
  - Bad: `feat(PROJ-123): add password reset flow`
  - Good: `feat(auth): add password reset flow`
- **Reference the ticket in the body/footer** on its own line: `Ticket: PROJ-123`, or `Closes
  PROJ-123` when it completes the work; a `Tickets:` block for multiple.
- Keep the subject on the *actual change*, not a version-bump label.

---

### Engineering defaults

- **All websites we author are responsive by default** — desktop, tablet, mobile from the outset.
  Mobile-first or fluid layouts, a `<meta name="viewport">`, sensible breakpoints. Responsiveness is
  a baseline acceptance criterion, not a later enhancement. Fixed-width/desktop-only only if I
  explicitly ask. (Third-party artefacts we merely host/display are exempt.)
- **Robust error handling** — specific exception types over generic; log with context; validate
  inputs; don't silence errors unless explicitly authorised and justified.
- **No backwards-compat shims for things you're rewriting.** Just change the code — there are no
  external consumers unless I say so.
- **No disposable validation scripts** — verify with the project's test framework, not throwaway
  scripts.
- **Config at the top** — user-customisable config variables at the head of scripts; feature-flag
  toggles rather than deleting functionality.
- **Security is paramount** — never embed real secrets; use clear placeholders (`YOUR_API_KEY`) and
  remind me to replace them; advise on env-vars/secret-management and `.gitignore`.

---

### Things never to do

- **Never sleep-poll** to wait for a background task — the harness notifies you on completion.
- **Don't create rival planning/analysis docs** outside the canon above unless explicitly asked.
- **Don't suppress bugs** unless explicitly authorised.

---

### How to resume work

0. Read **NIGHTNIGHT.md** — germane context to resume cleanly. Empty it once resumed.
1. Read **EPICS.md** — the snapshot table shows where we are and what's next.
2. Read **STORYMAP.md** — backbone + release slices show the journey shape and current slice / walking
   skeleton; cross-check against the EPICS tiers.
3. Read **SNAGGING.md** — the punch list, numbered by priority.
4. If I name something specific ("the mobile thing", "that login bug"), it's in SNAGGING.md — find it
   there.
5. Brand-new feature → add an Epic row + section in EPICS.md. Don't bloat SNAGGING with epic-sized
   work.
6. **Verify before recommending** — anything in these docs may have shifted. `git log`, `git diff`,
   `grep`, or just read the file. What's in the code is the source of truth.

---
---

# APPENDIX A — PRD MASTER TEMPLATE

<!--
  Use this structure for every PRD. Section names, ordering, the 8-column Requirements/Out-of-Scope
  table, and the controlled-vocabulary lozenges are the house standard — preserve them.
  Replace <angle-bracket> placeholders and delete guidance comments as you fill each section.

  Controlled vocabularies (keep as enums):
    Importance (phase): ALPHA | BETA | GTM | Future
    Persona involvement: SIGN-OFF | INFLUENCER | USER | DELIVERY | IN-LIFE SERVICE
  The Requirements and Out of Scope tables share the SAME 8 columns so an item can move
  in/out of scope just by changing its Importance value.
-->

# <Product / Initiative Name> — Product Requirements Document (PRD)

| **Planning Stage** | Concept → Ballpark → Initial Review → Initial Scoping → Estimation → Commercials → Sign-Off → Resourced → **In Flight** → Delivered → Launched |
| --- | --- |
| **Document owner** | @<name> |
| **Business Sponsor** | <group / sponsor> |
| **Product Owner** | @<name> |
| **Project Manager** | @<name> |
| **Technical Lead(s)** | @<name> |
| **Team(s)** | <delivery team(s)> |

## Overview
<!-- Elevator pitch: what this product is, the market position it establishes, the one-paragraph vision. What "winning" looks like. -->

## Customer Problem
<!-- The customer-side problem in prose: what users are trying to do, why it's hard today, the false choice / status quo they're stuck with. State the core problem as a single sharp sentence. -->

### Customer Pain Points

| Pain | Why it matters |
| --- | --- |
| <a specific customer pain> | <commercial / compliance / operational consequence> |

## Strategic Value
<!-- Why this matters to the BUSINESS. The strategic bet — defensive vs offensive angles, sector strategy, leverage of existing assets. Bold lead-ins per strand. -->

* **<Angle 1 (e.g. Defensive).>** <argument>
* **<Angle 2 (e.g. Offensive).>** <argument>

## Value Proposition

|  | **Value to Customer** | **Value to Us** |
| --- | --- | --- |
| **New Business** | <value> | <value> |
| **Existing Business** | <value> | <value> |
| **Partners** | <value> | <value> |

## Why now
<!-- The timing case. Why this window, why not later. Break into the distinct forces pulling the market. -->

### <Force 1 (e.g. Market pull)>
### <Force 2 (e.g. Regulatory / Security pull)>
### <Force N (e.g. Internal / Company pull)>

## Objectives
<!-- Numbered outcomes the initiative must achieve. Each starts with a bold verb phrase; outcome-oriented and measurable. -->

1. **<Objective>** — <detail>

## Constraints & Dependencies
<!-- What constrains delivery and what this depends on. Group by type; number continuously so each is referenceable. -->

**Delivery constraints**
1. **<Constraint>.** <why it bites>

**Internal dependencies**
2. **<Dependency>.** <relationship and risk>

**Vendor and partner dependencies**
3. **<Dependency>.** <relationship and risk>

**Regulatory dependencies**
4. **<Dependency>.** <relationship and risk>

## Assumptions
<!-- Premises the plan rests on. If any prove false, revisit the plan. Group by domain; number continuously. -->

### <Domain (e.g. Platform and architecture)>
1. <assumption>
### <Domain (e.g. Vendor and commercial)>
2. <assumption>
### <Domain (e.g. Market and customer)>
3. <assumption>

## Risks
<!-- Each risk owned and mitigated. Group by category; number continuously. State the threat then an italic _Mitigation:_. -->

### <Category (e.g. Strategic and commercial risks)>
1. **<Risk title>.** <threat>. _Mitigation:_ <mitigation>.
### <Category (e.g. Delivery risks)>
2. **<Risk title>.** <threat>. _Mitigation:_ <mitigation>.

## Persona
<!-- Who are the target personas, which is key, what value for each. One row per persona, grouped by Organization. Involvement lozenges: SIGN-OFF | INFLUENCER | USER | DELIVERY | IN-LIFE SERVICE. -->

| **Organization** | **Type** | **Persona** | **Involvement** | **Primary Value Sought** |
| --- | --- | --- | --- | --- |
| **Client** | `SIGN-OFF` | <persona> | <role in buying / using> | <what they want> |
| | `USER` | <persona> | <role> | <value sought> |
| **Us** | `DELIVERY` | <persona> | <role> | <value sought> |
| **Partner** | `DELIVERY` | <persona> | <role> | <value sought> |

## Core Motions
<!-- High-level "who does what" — the verbs of the platform (Deliver / Configure / Build / Test & Release / Monitor). One row per motion. -->

| **Use Case** | **Description** | **Primary Personas** |
| --- | --- | --- |
| **<Motion>** | <what happens> | <personas> |

## Spectrum of Use Cases
<!-- Key end-customer use cases, ordered simplest/highest-volume to most complex/mature. -->

| **Use Case** | **Description** |
| --- | --- |
| <use case> | <description, with value/ROI note if known> |

### Notes on Go to Market
<!-- How GTM differs by segment (new vs existing) and which use cases / sectors each motion leads with. -->

## Requirements
<!-- Core high-level requirements first, then a story-mapping approach. Each H3 is a story-map ACTIVITY; rows are requirement stubs written as user stories. Keep in sync with STORYMAP.md. Importance column uses phase lozenges. Repeat the 8-column table under each activity H3. -->

### <Activity / capability area, e.g. Deliver an enterprise platform>

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <short stub> | As a <persona>, I want <capability> so that <benefit>. | `ALPHA` | <persona> | <activity / action> | <step> | <ticket link> | <notes> |

### <Activity area 2>

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Out of Scope
<!-- Explicitly excluded requirements. Same 8-column table; set Importance to "Future" to mark deferred items. Makes scope boundaries auditable. -->

| **Requirement (stub)** | **User Story** | Importance | **Persona** | **Action** | **Step** | Ticket | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <short stub> | As a <persona>, I want <capability> so that <benefit>. | Future | <persona> | <action> | <step> |  |  |

## UX Design
<!-- Early sketches now; link to real designs as they land. If none yet, bullet what's known: which screens must exist, key flows, interaction patterns. -->

## Architecture & Technical Considerations
<!-- High-level architecture view and key technical considerations / known choices. Link to ARCHITECTURE.md when available. -->

1. <consideration>

## Success Metrics
<!-- Metrics that show you're hitting internal goals + how you'll measure customer success. Leading and outcome metrics. -->

## GTM Approach
<!-- Product messaging for existing and new customers; the launch plan across marketing and sales. -->

## Open Issues
<!-- What's still unresolved, problems that may arise, how you plan to address them. -->

## Q&A

| **Asked by** | **Date** | **Question** | **Answer** | **Answered By** | **Accepted By** | **Close Date** |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## Feature Timeline and Phasing
<!-- Indicative phasing (e.g. ALPHA → BETA → GTM → Future windows mapped to dates / milestones). -->

---
---

# APPENDIX B — STORYMAP TEMPLATE

# STORYMAP — <Product>

> Jeff Patton user story map. **Two views of one dataset:** this map and the PRD Requirements
> table — keep them in sync (the table's `Action`/`Step` columns are this map's Activities/Steps;
> `Importance` lozenges track the release slices). Re-cut whenever scope shifts. This map
> **drives the EPICS tiers** (Walking Skeleton = MTP, R2 = MVP, R3 = MSP, ribs = MLP).

**Narrative (the one-sentence JTBD goal above the backbone):**
_As <persona>, I <job> so that <outcome>._

---

## The map

Backbone (Activities — user *behaviours*, left→right in journey order): **A1 → A2 → A3 → …**

Under each activity: Steps, then Tasks. Tag every task with its release slice **(R1/R2/R3)** so the
horizontal cut is visible. Priority descends vertically.

### A1 — <activity: what the user is doing>
- **Step 1.1 — <observable action>**
  - <task> (R1)
  - <task> (R2)
- **Step 1.2 — <observable action>**
  - <task> (R1)
  - <task> (R3)

### A2 — <activity>
- **Step 2.1 — <observable action>**
  - <task> (R1)
  - <task> (R2)

### A3 — <activity>
- **Step 3.1 — <observable action>**
  - <task> (R1)
  - <task> (R3)

---

## Release slices (the horizontal cuts → EPICS tiers)

Every slice is a **thin slice across the whole backbone** — never one activity built fully before the
next.

### R1 · Walking Skeleton → **MTP**
The thinnest top-priority task across *every* activity — a complete end-to-end journey at its
simplest.
- A1: <task>
- A2: <task>
- A3: <task>

### R2 · Enhanced → **MVP** (demo-able)
- <tasks…>

### R3 · Polish → **MSP** (sellable)
- <tasks…>

### Below the line · Ribs → **MLP** (delight)
- <tasks…>

---

## From map to backlog

Each Task above slices into INVEST-sized user stories:
- Validate INVEST-minus-Small first; if a slice isn't *Valuable*, recombine rather than split; always
  **vertical** slices delivering observable user value — never horizontal splits.
- Write each story in Mike Cohn "As a / I want / so that" + Gherkin Given/When/Then form.
- Story-point at the story level; the slices become the EPICS.md tiers.
