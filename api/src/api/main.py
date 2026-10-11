"""ASGI application exposing the sales dataset over GraphQL.

Run locally with::

    uv run uvicorn api.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from api import __version__
from api.schema import schema

#: Vite's dev server. Deployment origins are added when the app is deployed.
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

app = FastAPI(
    title="Pharma FX Impact Dashboard API",
    version=__version__,
    description=(
        "Serves Sanofi public quarterly sales data transcribed from the "
        "official results press releases."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe. Useful on hosts that sleep idle containers."""
    return {"status": "ok", "version": __version__}
