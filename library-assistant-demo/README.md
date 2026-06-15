# Fort Smith Public Library — "Library Magic Assistant" concept demo

A clickable, **art-of-the-possible** prototype to show the library's leadership what
an AI assistant could do for customers. It is styled to echo the live
[fortsmithlibrary.org](https://www.fortsmithlibrary.org/) brand — navy logo block,
mauve "How can we help?" bands, teal quick-link tiles, coral *Give* button, and the
"Your Community Front Porch" tagline.

> ⚠️ **This is a mockup.** Everything runs in the browser on **sample data** — no real
> catalog, no customer records, no network calls. It is for discussion only and is not
> affiliated with or endorsed by the library.

## How to view it

Just open `index.html` in any browser (double-click it — no server, no build step).
Click **Ask Marian** (bottom-right) or any suggested prompt.

## The working name

The assistant is called **"Marian"** in this demo — a nod to Marian the Librarian.
It's a placeholder; swap it in one line (`ASSISTANT_NAME` in `app.js`). Other options
to float with the CEO:

| Name | Angle |
|------|-------|
| **Marian** | Warm, classic librarian reference; friendly |
| **Belle** | Local flavor (Belle Starr) + "belle of the library" |
| **Sparrow / Spark** | "Spark a love of reading"; modern |
| **Ada** | Ada Lovelace; smart, gender-neutral-ish |
| **Porch** | Plays directly off "Your Community Front Porch" |
| **Ask FSPL / The Desk** | Plain, institutional, no persona to maintain |

## What the demo shows (the six asks)

Each is wired up with realistic sample data so you can click through live:

1. **Suggested prompts** — chips for *Location & hours*, *Next story time*, *Find a
   book*, *Reserve a book*, *Kids' book ideas*, *Interlibrary loan*, *What's happening
   this week*, *Research help*.
2. **Natural-language find + reserve against real-time inventory** — ask for a book,
   see live availability across all four branches (Main, Dallas, Miller, Windsor
   Drive), and place a hold with a pickup branch. Books with no copies show the hold
   queue instead.
3. **Interlibrary loan (ILL)** — when a title isn't owned, the assistant offers to
   submit an ILL request from a partner library.
4. **Age-appropriate suggestions** — "books for my 7-year-old" → right-leveled picks
   (picture / early reader / middle-grade / YA / adult), with a caregiver content note.
5. **Database links + augmented research** — routes research questions to the right
   licensed databases (Ancestry, Gale, Mango, etc.) and *augments* with a few **cited**
   open-web starting points (the "additional feature").
6. **Event search** — find programs and story times by age, branch, or day.

## How the *real* thing would be built (the architecture story)

The core idea you wanted to convey — **expose the catalog as a read-only view that
natural language can safely query** — is both the most valuable and the safest place to
start. Here's the shape of it:

```
            Customer (web / mobile / kiosk / phone)
                          │  plain-English question
                          ▼
                ┌───────────────────────┐
                │   Assistant (LLM)      │  intent + grounding, no free-form DB access
                │  guardrails + prompts  │
                └───────────┬───────────┘
                            │ structured, whitelisted calls only
            ┌───────────────┼───────────────────────────┐
            ▼               ▼                            ▼
   READ-ONLY catalog   Official write APIs        Licensed DBs + web
   view / replica      (Polaris PAPI):            (Ancestry, Gale… +
   (availability,      place hold, ILL,           cited open sources)
    holdings, events)  account — authenticated
```

Key decisions that make this responsible:

- **Read replica, not the production ILS.** Fort Smith runs **Polaris** (the catalog
  lives at `catalog.fortsmithlibrary.org/polaris`). Stand up a **read-only replica or a
  nightly/near-real-time export** of just the *bibliographic + availability* data. The
  assistant queries that — it physically **cannot** write to or lock the live system.
- **No customer PII in the read view.** Holdings and availability are not personal data.
  Anything account-specific (your holds, your card) goes through Polaris's **official
  authenticated APIs (PAPI/web services)**, scoped per-session, never scraped.
- **The LLM doesn't write SQL against your database.** It calls a small set of
  **whitelisted, parameterized functions** ("search availability", "place hold",
  "submit ILL"). This is the single most important safety property — it prevents prompt
  injection from turning into data exposure or a destructive query.
- **Grounded answers only.** Recommendations and research come *with citations* (catalog
  records, database entries, named sources) so staff and customers can trust them and
  there's no fabrication.
- **Full audit + human escalation.** Every action is logged; anything ambiguous (a fine
  dispute, a sensitive request) hands off to staff/existing chat.

A realistic phased rollout:

- **Phase 1 (weeks, low risk):** read-only Q&A — hours, locations, events, "is this on
  the shelf?", recommendations. No writes at all. This alone is a big win and validates
  demand.
- **Phase 2:** authenticated actions — place holds, ILL requests, renewals — through
  Polaris's official APIs.
- **Phase 3:** research augmentation, multilingual support, voice/phone, kiosk mode.

## Is this a good idea?

**Short answer: yes — as a customer-facing concierge over a read-only catalog view,
starting with read-only Q&A. That scoping is what makes it safe, cheap, and genuinely
useful.** A few honest caveats to raise *with* the CEO so the pitch is credible:

**Why it's compelling**
- Meets people in plain language, 24/7, in any language — extends the reference desk
  without adding staff hours.
- Lowers the barrier for exactly the customers libraries most want to reach: kids'
  caregivers, job seekers, new-to-research users, non-English speakers.
- The hardest-sounding ask (live inventory + reserve) is actually well-trodden: Polaris
  already exposes availability and has official APIs for holds/ILL. We're adding a
  natural-language front door, not rebuilding the ILS.
- Showcases the library as modern and forward-leaning — good for funders and the board.

**What to be honest about**
- **Accuracy & trust.** An assistant that invents a due date or a program time erodes
  trust fast. Mitigation: ground every answer in real records + citations; never let the
  model free-text facts it can't cite.
- **Vendor reality.** Capabilities depend on what Polaris/Innovative permits via API and
  licensing. Worth a quick confirmation call before committing to Phase 2 features.
- **Database licensing.** Many licensed databases (Ancestry Library Edition, etc.) are
  *in-building* or session-bound; the assistant can *route* to them but can't relicense
  their content. Keep "augmented research" to **cited links + open sources**, not
  re-hosting paywalled material.
- **Privacy & equity.** Library customer records are legally protected and politically
  sensitive. Keep PII out of the AI layer, be transparent that it's an assistant, and
  keep a human path. Also keep the **non-AI** catalog/site fully usable — the assistant
  augments, never replaces.
- **Cost & maintenance.** It's a product, not a one-off: hosting, model costs, content
  upkeep, and staff training. Phase 1 keeps this small while you prove value.

**Recommended pitch framing:** "A natural-language front porch to the catalog we already
have — read-only first, customer-friendly, with citations and a human always one click
away." Demo Phase 1 live (this mockup), name Phase 2/3 as the roadmap.

## Files

**Interactive demo**
- `index.html` — the branded homepage + assistant launcher/panel
- `styles.css` — palette + layout matched to the live site
- `app.js` — sample data (catalog, branches, hours, events, databases) + the rules
  engine that stands in for the LLM's intent routing
- `library-magic-assistant-demo.html` — **single-file build** (CSS + JS inlined); email
  it or drop it on a tablet/kiosk — opens with no server. Rebuild via
  `node build-standalone.cjs`.

**Leave-behinds for the meeting**
- `proposal.html` / `Library-Magic-Assistant-Proposal.pdf` — the **2-page proposal + cost
  appendix** (vision, architecture, governance, phased roadmap, next steps, hosting, and a
  run-cost envelope: per-conversation + monthly-by-volume + on-prem vs cloud). Open
  `proposal.html` and Print → Save as PDF to regenerate.
- `BUSINESS-NOTES.md` — analysis of standing up a managed-AI-for-orgs business.

**Proposed data layer (the catalog as a read-only, PII-free surface)**
- `sql/polaris-ai-views.sql` — proposed **SQL Server (Polaris) read-only views** the
  assistant iterates over: title metadata (MARC-derived), real-time per-branch
  availability, aggregate hold demand, new arrivals, and a denormalized discovery blob
  for embeddings. Includes schema-discovery query + least-privilege grants.
- `sql/pgvector-repository.sql` — downstream **Postgres + pgvector** repository the tool
  searches (mirrors this repo's Supabase + Ollama stack), plus the sync sketch.

**This document** — `README.md`

### The proposed data flow, end to end

```
Polaris (SQL Server)  ──►  ai.* read-only views  ──►  nightly sync + embed (Ollama)
   live availability         (no PII)                       │
        │                                                   ▼
        └────────── live re-check before a hold ──►  Postgres + pgvector (catalog_titles)
                                                            │
                                          assistant retrieves + grounds answers (cited)
```
