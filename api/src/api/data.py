"""Loading and typing of the transcribed sales dataset.

The dataset is a small, version-controlled JSON file read once at import.
There is no database: see ``data/README.md`` for sources and assumptions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

DATA_FILE: Final = Path(__file__).resolve().parents[2] / "data" / "sales.json"

#: China is published as a subset of Rest of World and must never be added to
#: the regional total. Resolvers expose it, callers filter on ``subset_of``.
REST_OF_WORLD: Final = "Rest of World"

#: Appendix 1 lines that aggregate many products rather than naming one. They
#: are needed for totals to reconcile, but must not rank as "top products".
AGGREGATE_PRODUCT_LINES: Final = frozenset({"Others", "Industrial Sales"})


@dataclass(frozen=True, slots=True)
class RegionSales:
    """Net sales for one geography, as published under 'Sales by geography'."""

    region: str
    net_sales_eur_m: int
    cer_growth_pct: float | None
    subset_of: str | None


@dataclass(frozen=True, slots=True)
class ProductRegionSales:
    """One product's sales within one geography."""

    region: str
    net_sales_eur_m: int | None
    cer_growth_pct: float | None


@dataclass(frozen=True, slots=True)
class ProductSales:
    """One medicine or vaccine line from the quarter's Appendix 1 table."""

    name: str
    therapeutic_area: str
    net_sales_eur_m: int
    cer_growth_pct: float | None
    reported_growth_pct: float | None
    by_region: tuple[ProductRegionSales, ...]

    @property
    def is_aggregate(self) -> bool:
        """True for catch-all lines such as 'Others' and 'Industrial Sales'."""
        return self.name in AGGREGATE_PRODUCT_LINES


@dataclass(frozen=True, slots=True)
class CompanyFigures:
    """Company-level reconciliation of net sales to sales at CER.

    Satisfies two identities, verified for every quarter in the dataset::

        cer_sales_eur_m    = net_sales_eur_m - fx_effect_eur_m
        reported_growth_pct = cer_growth_pct + fx_impact_pp
    """

    net_sales_eur_m: int
    fx_effect_eur_m: int
    cer_sales_eur_m: int
    cer_growth_pct: float
    fx_impact_pp: float
    reported_growth_pct: float


@dataclass(frozen=True, slots=True)
class AverageRate:
    """Published average exchange rate against the euro for the period.

    Sanofi publishes both the comparative and the current period rate, which
    is what a CER recalculation needs.
    """

    currency: str
    comparative_rate: float
    current_rate: float


@dataclass(frozen=True, slots=True)
class Quarter:
    """One quarterly results release."""

    id: str
    label: str
    published_on: str
    source_url: str
    comparative_period: str
    company: CompanyFigures
    regions: tuple[RegionSales, ...]
    average_rates: tuple[AverageRate, ...]
    products: tuple[ProductSales, ...]


@dataclass(frozen=True, slots=True)
class CurrencySensitivity:
    """Disclosed sensitivity of net sales to a given rate movement."""

    currency: str
    variation: str
    net_sales_impact_eur_m: int


@dataclass(frozen=True, slots=True)
class CurrencyExposure:
    """Share of net sales denominated in a given currency."""

    currency: str
    share_of_sales_pct: float


@dataclass(frozen=True, slots=True)
class Company:
    """A reporting company and its quarters.

    The dataset is keyed by company so a second reporter can be added as data
    rather than as a schema change. Only companies that publish their own FX
    effect can be represented — that figure is not available from any API.
    """

    id: str
    name: str
    reporting_currency: str
    segment: str
    sensitivities_basis: str
    sensitivities_source_url: str
    currency_sensitivities: tuple[CurrencySensitivity, ...]
    exposure_basis: str
    exposure_source_url: str
    currency_exposure: tuple[CurrencyExposure, ...]
    quarters: tuple[Quarter, ...]


def _region(raw: dict[str, Any]) -> RegionSales:
    return RegionSales(
        region=raw["region"],
        net_sales_eur_m=raw["netSalesEurM"],
        cer_growth_pct=raw["cerGrowthPct"],
        subset_of=raw["subsetOf"],
    )


def _product(raw: dict[str, Any]) -> ProductSales:
    return ProductSales(
        name=raw["name"],
        therapeutic_area=raw["therapeuticArea"],
        net_sales_eur_m=raw["netSalesEurM"],
        cer_growth_pct=raw["cerGrowthPct"],
        reported_growth_pct=raw["reportedGrowthPct"],
        by_region=tuple(
            ProductRegionSales(
                region=r["region"],
                net_sales_eur_m=r["netSalesEurM"],
                cer_growth_pct=r["cerGrowthPct"],
            )
            for r in raw["byRegion"]
        ),
    )


def _quarter(raw: dict[str, Any]) -> Quarter:
    c = raw["company"]
    return Quarter(
        id=raw["id"],
        label=raw["label"],
        published_on=raw["publishedOn"],
        source_url=raw["sourceUrl"],
        comparative_period=raw["comparativePeriod"],
        company=CompanyFigures(
            net_sales_eur_m=c["netSalesEurM"],
            fx_effect_eur_m=c["fxEffectEurM"],
            cer_sales_eur_m=c["cerSalesEurM"],
            cer_growth_pct=c["cerGrowthPct"],
            fx_impact_pp=c["fxImpactPp"],
            reported_growth_pct=c["reportedGrowthPct"],
        ),
        regions=tuple(_region(r) for r in raw["regions"]),
        average_rates=tuple(
            AverageRate(
                currency=r["currency"],
                comparative_rate=r["comparativeRate"],
                current_rate=r["currentRate"],
            )
            for r in raw["averageRates"]
        ),
        products=tuple(_product(p) for p in raw["products"]),
    )


def _company(raw: dict[str, Any]) -> Company:
    sens = raw["currencySensitivities"]
    exp = raw["currencyExposure"]
    return Company(
        id=raw["id"],
        name=raw["name"],
        reporting_currency=raw["reportingCurrency"],
        segment=raw["segment"],
        sensitivities_basis=sens["basis"],
        sensitivities_source_url=sens["sourceUrl"],
        currency_sensitivities=tuple(
            CurrencySensitivity(
                currency=e["currency"],
                variation=e["variation"],
                net_sales_impact_eur_m=e["netSalesImpactEurM"],
            )
            for e in sens["entries"]
        ),
        exposure_basis=exp["basis"],
        exposure_source_url=exp["sourceUrl"],
        currency_exposure=tuple(
            CurrencyExposure(
                currency=e["currency"], share_of_sales_pct=e["shareOfSalesPct"]
            )
            for e in exp["entries"]
        ),
        quarters=tuple(_quarter(q) for q in raw["quarters"]),
    )


@lru_cache(maxsize=1)
def load_companies(path: Path | None = None) -> tuple[Company, ...]:
    """Read and parse the dataset. Cached: the file is static and read-only."""
    raw = json.loads((path or DATA_FILE).read_text(encoding="utf-8"))
    return tuple(_company(c) for c in raw["companies"])


def find_company(company_id: str) -> Company | None:
    """Return the company with this id, or ``None`` if it is not in the dataset."""
    return next((c for c in load_companies() if c.id == company_id), None)


def find_quarter(company_id: str, quarter_id: str) -> Quarter | None:
    """Return one quarter for one company, or ``None`` if either is unknown."""
    company = find_company(company_id)
    if company is None:
        return None
    return next((q for q in company.quarters if q.id == quarter_id), None)
