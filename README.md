# Pharma FX Impact Dashboard

Sanofi sells worldwide in many currencies but reports in EUR. This dashboard
answers one question: **did sales really grow, or did exchange rates make it
look that way?**

It is a portfolio project built on Sanofi's **public quarterly results data**.
It is not a Sanofi product and carries no Sanofi branding.

> **Status:** in development. See [Roadmap](#roadmap) for what is built so far.

## Screenshot

_Placeholder — to be added once the overview and waterfall views are in._

## Why it exists

A finance controller looking at "+6.2% sales growth" cannot tell how much of
that is real commercial performance and how much is the euro moving against
the dollar. Sanofi reports both figures, but separately and in PDFs. This app
puts reported growth and constant-exchange-rate (CER) growth side by side, then
lets you move FX rates yourself to see what happens.

Worked example, from Q1 2026: sales grew **+13.6% at CER**, but currency
movements cost **7.4 percentage points**, so the reported figure was **+6.2%**.
Same business performance, very different headline.

## Architecture

```
┌─────────────────────────┐        GraphQL        ┌──────────────────────────┐
│  web/  React + Vite     │ ───────────────────►  │  api/  FastAPI +         │
│                         │                       │        Strawberry        │
│  Redux Toolkit          │                       │                          │
│  RTK Query ─────────────┼──── REST ──────────►  │  api/data/sales.json     │
│  Recharts + D3          │   Frankfurter API     │  (transcribed from        │
│                         │   (ECB rates)         │   press releases)        │
└─────────────────────────┘                       └──────────────────────────┘
```

- **`api/`** serves the transcribed sales data over GraphQL. No database — the
  dataset is small, versioned JSON with a source URL on every record.
- **`web/`** uses a single RTK Query setup for both sources: a GraphQL base
  query for our API, plain REST for live FX rates.
- **FX and CER maths** live in one pure, typed, React-free module with unit
  tests asserting against Sanofi's own published reconciliation figures.

## Running locally

Requires **Node 20+** and **Python 3.14+** with [uv](https://docs.astral.sh/uv/).

```bash
# API — http://localhost:8000  (serves GraphQL from Phase 1)
cd api
uv sync
uv run uvicorn api.main:app --reload

# Web — http://localhost:5173
cd web
npm install
npm run dev
```

### Checks

```bash
cd web && npm run lint && npm run typecheck && npm test
cd api && uv run pytest
```

## Data sources and assumptions

All sales figures come from Sanofi's official quarterly results press releases.
Nothing is invented, estimated or rounded to fill a gap — if a figure is not
published, it is left out and noted in [`api/data/README.md`](api/data/README.md).

Quarters currently covered: **Q1 2025, Q2 2025, Q3 2025, Q1 2026**.

| Quarter | Net sales | FX effect | CER sales | CER growth | FX impact | Reported |
| ------- | --------- | --------- | --------- | ---------- | --------- | -------- |
| Q1 2025 | €9,895m   | +€98m     | €9,797m   | +9.7%      | +1.1pp    | +10.8%   |
| Q2 2025 | €9,994m   | −€384m    | €10,378m  | +10.1%     | −4.1pp    | +6.0%    |
| Q3 2025 | €12,434m  | −€578m    | €13,012m  | +7.0%      | −4.7pp    | +2.3%    |
| Q1 2026 | €10,509m  | −€733m    | €11,242m  | +13.6%     | −7.4pp    | +6.2%    |

**Key assumption.** Sanofi publishes FX impact at company level, not per region.
To attribute currency effects to individual regions, each region is mapped to a
currency or basket (United States → USD, China → CNY, and so on). This is an
approximation and the app says so: the validation view compares the
approximated CER growth against Sanofi's published CER growth and shows the
difference, rather than hiding it.

Live exchange rates come from the [Frankfurter API](https://frankfurter.dev/)
(ECB reference rates, no API key required).

## Roadmap

- [x] **Phase 0** — toolchains, strict TypeScript, test setup for both packages
- [ ] **Phase 1** — sales data model and GraphQL API
- [ ] **Phase 2** — frontend data layer (RTK Query, GraphQL + REST)
- [ ] **Phase 3** — sales overview: reported vs CER growth
- [ ] **Phase 4** — FX/CER calculation module with unit tests
- [ ] **Phase 5** — FX impact waterfall (D3)
- [ ] **Phase 6** — what-if currency scenario sliders
- [ ] **Phase 7** — drill-down: total → business unit → region → products
- [ ] **Phase 8** — validation against published CER figures
- [ ] **Phase 9** — CI (lint, typecheck, test)
- [ ] **Phase 10** — full documentation

## Out of scope

Authentication, a database, user accounts, and Sanofi branding.

## Licence and attribution

Project code is for portfolio purposes. Sanofi's published financial figures
remain the property of Sanofi and are used here as public reference data with
sources cited.
