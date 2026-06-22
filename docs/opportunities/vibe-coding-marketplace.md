# Opportunity: Vibe-Coding Talent Marketplace

> Parked for future consideration. Researched 2026-06-22 via the "council" (5-agent
> deliberation). Destined for a tile on **Commander / Control Center**
> (`jculberson/dashboard`, dash.wdjj.cc) — staged here because that repo is outside
> this session's scope.

## Commander tile (ready to import)

```json
{
  "title": "Vibe-Coding Talent Marketplace",
  "category": "Business idea — parked for future consideration",
  "council_score": "2.5/5 as a plain job board · ~4/5 if pivoted to vetting-led",
  "status": "Researched",
  "one_liner": "Hire AI-native builders whose work is already shipped & stress-tested — proof-of-work, not résumés.",
  "verdict": "Wave is real (Cursor ~$2B ARR, Lovable $200M ARR, ~90% dev AI adoption); the job-board format is weak — already cloned (GoodVibeCode, VibeCodeCareers), no moat, two-sided cold-start, and the term itself is fading (Karpathy called 'vibe coding' passe, Feb 2026).",
  "killer_value_prop": "Trust/verification layer + escrow, wedged into non-technical founders needing an MVP.",
  "recommended_wedge": "Start single-sided: (1) security/QA audits for vibe-coded apps (58% had a critical vuln in one scan) -> (2) newsletter/community as audience -> (3) vetting-led marketplace last, into an owned audience.",
  "top_risks": ["Two-sided cold-start", "Zero defensibility vs LinkedIn/Upwork", "Buzzword decay 12-24mo", "Skill hard to screen"],
  "next_step": "Validate willingness-to-pay for the audit service before building any marketplace.",
  "full_memo": "docs/opportunities/vibe-coding-marketplace.md"
}
```

## Council verdict (full)

**Bottom line:** A plain vibe-coding *job board* is a weak bet (consensus ~2.5/5) — the
wave is real and huge, but the "job board" format is the wrong shape for it:
commoditized, indefensible, and two-sided cold-start. The opportunity is real; the format
is wrong.

| Council member | Score | Take |
|---|---|---|
| Market Analyst | 3/5 | Megatrend tools, but the *term* is peaking — don't brand on it |
| Skeptical VC | 2/5 | Commodity board, no moat, incumbents index it for free — avoid |
| Marketplace Operator | 4/5 | Operable solo, but already cloned — win with **audience**, not the board |
| Product/GTM | (pivot) | Build a **vetting-led talent network with escrow**, not a board |
| Adjacent Scout | (pivot) | Easier single-sided plays exist — start with **security audits** |

### Killer value proposition
> "Hire a vibe coder whose work we've already shipped and stress-tested — proof-of-work,
> not résumés. If the build breaks, you don't pay."

Anchor every profile to a live deployed app + automated security/maintainability scan +
milestone escrow. Wedge: **non-technical founders who need an MVP** (highest trust-pain,
least able to self-vet). Market emotion is fear: ~84% adoption but only ~29% trust;
~45% of AI-generated code carries OWASP Top-10 vulns.

### Obstacles
1. Two-sided cold-start (mitigate: aggregate existing AI-coding listings day one).
2. Zero defensibility vs. LinkedIn / Wellfound / Upwork (need a vetting/trust asset).
3. Disintermediation once matched (escrow + guarantees keep value on-platform).
4. Buzzword decay — decouple the business from "vibe coding"; use it as SEO copy only.
5. Monetization on a cold audience (can't charge for posts with no traffic).
6. Skill is hard to screen — which is exactly why a verification rubric is the wedge.

### Easier adjacent problems (single-sided / pick-and-shovel)
1. **Security/QA audits for vibe-coded apps** (start here) — one-sided, acute pain
   (58% critical-vuln rate in one scan of 1,400+ apps), time-to-first-dollar 1-3 weeks.
2. **"We vibe-code your MVP" done-for-you agency** — fastest cash, low defensibility.
3. **Curated newsletter + paid community** — audience-first; the audience later becomes
   the supply side if a marketplace is ever built.

### Recommended sequence
Security-audit service (cash + credibility, teaches the vetting rubric) →
newsletter/community (distribution) → vetting-led marketplace with escrow, launched into
an owned audience. Marketplace last, only once one side is captive.

> Working assumptions: solo/bootstrapped founder; "vibe coding" = building software
> primarily by prompting AI (Cursor, Claude Code, Lovable, v0, Replit Agent, Bolt).
