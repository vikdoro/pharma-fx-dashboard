# api

GraphQL API serving Sanofi public quarterly sales data for the Pharma FX
Impact Dashboard.

Built with FastAPI + [Strawberry GraphQL](https://strawberry.rocks/), managed
with [uv](https://docs.astral.sh/uv/). Requires Python 3.14+.

## Running

```bash
uv sync
uv run uvicorn api.main:app --reload
```

- GraphQL endpoint and interactive playground: http://localhost:8000/graphql
- Health probe: http://localhost:8000/health

An example query:

```graphql
{
  company {
    name
    latestQuarter {
      label
      company { netSalesEurM cerGrowthPct fxImpactPp reportedGrowthPct }
      topLevelRegions { region netSalesEurM cerGrowthPct }
      topProducts(limit: 5) { name netSalesEurM therapeuticArea }
    }
  }
}
```

## Tests

```bash
uv run pytest
```

64 tests, split three ways:

- `test_dataset.py` — integrity of the data itself: both published identities
  hold per quarter, regions and products reconcile with the company total,
  China is never double counted, and every quarter carries its source URL.
- `test_schema.py` — the GraphQL resolvers, including unknown ids returning
  null rather than erroring.
- `test_main.py` — the ASGI app: health probe, GraphQL endpoint, CORS.

## Layout

```
src/api/
  data.py       dataset loading, typed as frozen dataclasses
  schema.py     Strawberry GraphQL types and resolvers
  main.py       FastAPI app mounting /graphql
tests/          pytest suite
data/           sales.json + data provenance notes
```

No figure is computed here. FX and CER arithmetic lives in the frontend's pure
calculation module (Phase 4), so the API stays a typed, read-only view of what
Sanofi actually published.

## Data

There is no database. The dataset is small and version-controlled as JSON in
`data/sales.json`, transcribed by hand from Sanofi's quarterly results press
releases. Every record carries the quarter and the source URL it came from.

It is keyed by company, with Sanofi as the only entry. Only companies that
publish their own FX effect can be represented — that figure is a non-IFRS
measure and is not available from any financial data API — so adding a second
reporter is a transcription task rather than a schema change.

See [`data/README.md`](data/README.md) for sources, the region-to-currency
mapping, and known gaps.
