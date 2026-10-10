# web

Frontend for the Pharma FX Impact Dashboard: React + TypeScript (strict) on
Vite. Requires Node 20+.

## Running

```bash
npm install
npm run dev     # http://localhost:5173
```

Expects the GraphQL API on http://localhost:8000 — see [`../api`](../api).

## Scripts

| Script                  | Purpose                            |
| ----------------------- | ---------------------------------- |
| `npm run dev`           | Dev server with HMR                |
| `npm run build`         | Typecheck, then production build   |
| `npm run preview`       | Serve the production build         |
| `npm run lint`          | ESLint                             |
| `npm run typecheck`     | TypeScript, no emit                |
| `npm test`              | Vitest, single run                 |
| `npm run test:watch`    | Vitest, watch mode                 |
| `npm run test:coverage` | Vitest with v8 coverage            |

## Stack

- **State and data** — Redux Toolkit + RTK Query. One API setup serves both
  sources: a GraphQL base query for our API, plain REST for live FX rates from
  the [Frankfurter API](https://frankfurter.dev/).
- **Charts** — Recharts for standard charts, D3 for the custom FX waterfall.
- **Routing** — React Router, with drill-down filters synced to the URL so any
  view can be shared or reloaded.
- **Tests** — Vitest + Testing Library, co-located as `Foo.tsx` +
  `Foo.test.tsx`.

## Layout

```
src/components/        reusable chart and KPI components
src/features/<name>/   feature-scoped code
src/test/              test setup
```

FX and CER calculations deliberately live in a single pure, typed module with
no React dependency, so they can be unit tested directly against Sanofi's
published reconciliation figures.

## Conventions

- TypeScript strict, plus `noUncheckedIndexedAccess`.
- Every data view handles loading, error and empty states.
- Figures formatted as EUR millions to one decimal place, tabular numerals.
- Neutral palette via CSS custom properties in `src/index.css`; chart colours
  chosen to stay distinguishable and legible.
