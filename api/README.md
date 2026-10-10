# api

GraphQL API serving Sanofi public quarterly sales data for the Pharma FX
Impact Dashboard.

Built with FastAPI + [Strawberry GraphQL](https://strawberry.rocks/), managed
with [uv](https://docs.astral.sh/uv/). Requires Python 3.14+.

## Running

```bash
uv sync
uv run uvicorn api.main:app --reload   # available from Phase 1
```

- GraphQL endpoint and interactive playground: http://localhost:8000/graphql

## Tests

```bash
uv run pytest
```

Tests cover the GraphQL resolvers and the internal consistency of the sales
dataset — that totals match the sum of their parts, and that every record
carries a source URL and quarter.

## Layout

```
src/api/        application code
tests/          pytest suite
data/           sales.json + data provenance notes
```

The ASGI app (`src/api/main.py`) and `data/sales.json` arrive in Phase 1.

## Data

There is no database. The dataset is small and version-controlled as JSON in
`data/sales.json`, transcribed by hand from Sanofi's quarterly results press
releases. Every record carries the quarter and the source URL it came from.

See [`data/README.md`](data/README.md) for sources, the region-to-currency
mapping, and known gaps.
