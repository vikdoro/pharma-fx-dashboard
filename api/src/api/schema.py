"""GraphQL schema for the sales dataset.

Read-only. The resolvers map the dataclasses in :mod:`api.data` onto GraphQL
types; no figure is computed here. FX and CER arithmetic lives in the
frontend's pure calculation module, so the API stays a typed view of what
Sanofi actually published.
"""

from __future__ import annotations

import strawberry

from api import data


@strawberry.type(description="Net sales for one geography, as published.")
class RegionSales:
    region: str
    net_sales_eur_m: int = strawberry.field(description="Net sales in EUR millions.")
    cer_growth_pct: float | None = strawberry.field(
        description="Growth at constant exchange rates, in percent."
    )
    subset_of: str | None = strawberry.field(
        description=(
            "Set when this geography is reported inside another one. China is a "
            "subset of Rest of World and must not be added to the regional total."
        )
    )


@strawberry.type(description="One product's net sales within one geography.")
class ProductRegionSales:
    region: str
    net_sales_eur_m: int | None = strawberry.field(
        description="Net sales in EUR millions, or null where not published."
    )
    cer_growth_pct: float | None


@strawberry.type(description="One medicine or vaccine from the quarter's appendix.")
class ProductSales:
    name: str
    therapeutic_area: str = strawberry.field(
        description=(
            "Therapeutic area as grouped in the release. Sanofi reports a single "
            "Biopharma segment, so this is the finest published grouping above "
            "the product itself."
        )
    )
    net_sales_eur_m: int
    cer_growth_pct: float | None
    reported_growth_pct: float | None = strawberry.field(
        description="Growth at actual exchange rates, in percent."
    )
    is_aggregate: bool = strawberry.field(
        description=(
            "True for catch-all appendix lines such as 'Others' and "
            "'Industrial Sales'. They are needed for totals to reconcile but "
            "do not name a single product."
        )
    )
    by_region: list[ProductRegionSales]


@strawberry.type(
    description=(
        "Company-level reconciliation of net sales to sales at CER. "
        "A negative fxEffectEurM means currency movements reduced reported "
        "EUR sales, so sales at CER exceed net sales."
    )
)
class CompanyFigures:
    net_sales_eur_m: int
    fx_effect_eur_m: int = strawberry.field(
        description="Effect of exchange rates in EUR millions, signed."
    )
    cer_sales_eur_m: int
    cer_growth_pct: float
    fx_impact_pp: float = strawberry.field(
        description="Currency contribution to reported growth, in percentage points."
    )
    reported_growth_pct: float


@strawberry.type(
    description=(
        "Published average exchange rate against the euro. Both the "
        "comparative and current period rate are given, which is what a CER "
        "recalculation needs."
    )
)
class AverageRate:
    currency: str
    comparative_rate: float
    current_rate: float


@strawberry.type(description="One quarterly results release.")
class Quarter:
    id: str
    label: str
    published_on: str
    source_url: str = strawberry.field(
        description="The press release every figure in this quarter came from."
    )
    comparative_period: str = strawberry.field(
        description="The prior-year period growth figures are measured against."
    )
    company: CompanyFigures
    regions: list[RegionSales]
    average_rates: list[AverageRate]
    products: list[ProductSales]

    @strawberry.field(
        description=(
            "Regions excluding any that are a subset of another, so the values "
            "sum to the company total without double counting China."
        )
    )
    def top_level_regions(self) -> list[RegionSales]:
        return [r for r in self.regions if r.subset_of is None]

    @strawberry.field(
        description=(
            "Named products in this quarter, largest first. Aggregate lines "
            "such as 'Others' are excluded unless includeAggregates is set."
        )
    )
    def top_products(
        self, limit: int = 10, include_aggregates: bool = False
    ) -> list[ProductSales]:
        candidates = [
            p for p in self.products if include_aggregates or not p.is_aggregate
        ]
        ranked = sorted(candidates, key=lambda p: p.net_sales_eur_m, reverse=True)
        return ranked[:limit]


@strawberry.type(description="Disclosed sensitivity of net sales to a rate movement.")
class CurrencySensitivity:
    currency: str
    variation: str
    net_sales_impact_eur_m: int


@strawberry.type(description="Share of net sales denominated in a given currency.")
class CurrencyExposure:
    currency: str
    share_of_sales_pct: float


@strawberry.type(
    description=(
        "A reporting company. Only companies that publish their own FX effect "
        "can be represented, since that figure is not available from any API."
    )
)
class Company:
    id: str
    name: str
    reporting_currency: str
    segment: str
    sensitivities_basis: str
    sensitivities_source_url: str
    currency_sensitivities: list[CurrencySensitivity]
    exposure_basis: str
    exposure_source_url: str
    currency_exposure: list[CurrencyExposure]
    quarters: list[Quarter]

    @strawberry.field(description="One quarter by id, or null if unknown.")
    def quarter(self, id: str) -> Quarter | None:
        return next((q for q in self.quarters if q.id == id), None)

    @strawberry.field(description="The most recently published quarter.")
    def latest_quarter(self) -> Quarter | None:
        if not self.quarters:
            return None
        return max(self.quarters, key=lambda q: q.published_on)


def _to_graphql(company: data.Company) -> Company:
    """Map a dataset company onto its GraphQL type."""
    return Company(
        id=company.id,
        name=company.name,
        reporting_currency=company.reporting_currency,
        segment=company.segment,
        sensitivities_basis=company.sensitivities_basis,
        sensitivities_source_url=company.sensitivities_source_url,
        currency_sensitivities=[
            CurrencySensitivity(
                currency=s.currency,
                variation=s.variation,
                net_sales_impact_eur_m=s.net_sales_impact_eur_m,
            )
            for s in company.currency_sensitivities
        ],
        exposure_basis=company.exposure_basis,
        exposure_source_url=company.exposure_source_url,
        currency_exposure=[
            CurrencyExposure(
                currency=e.currency, share_of_sales_pct=e.share_of_sales_pct
            )
            for e in company.currency_exposure
        ],
        quarters=[
            Quarter(
                id=q.id,
                label=q.label,
                published_on=q.published_on,
                source_url=q.source_url,
                comparative_period=q.comparative_period,
                company=CompanyFigures(
                    net_sales_eur_m=q.company.net_sales_eur_m,
                    fx_effect_eur_m=q.company.fx_effect_eur_m,
                    cer_sales_eur_m=q.company.cer_sales_eur_m,
                    cer_growth_pct=q.company.cer_growth_pct,
                    fx_impact_pp=q.company.fx_impact_pp,
                    reported_growth_pct=q.company.reported_growth_pct,
                ),
                regions=[
                    RegionSales(
                        region=r.region,
                        net_sales_eur_m=r.net_sales_eur_m,
                        cer_growth_pct=r.cer_growth_pct,
                        subset_of=r.subset_of,
                    )
                    for r in q.regions
                ],
                average_rates=[
                    AverageRate(
                        currency=r.currency,
                        comparative_rate=r.comparative_rate,
                        current_rate=r.current_rate,
                    )
                    for r in q.average_rates
                ],
                products=[
                    ProductSales(
                        name=p.name,
                        therapeutic_area=p.therapeutic_area,
                        net_sales_eur_m=p.net_sales_eur_m,
                        cer_growth_pct=p.cer_growth_pct,
                        reported_growth_pct=p.reported_growth_pct,
                        is_aggregate=p.is_aggregate,
                        by_region=[
                            ProductRegionSales(
                                region=b.region,
                                net_sales_eur_m=b.net_sales_eur_m,
                                cer_growth_pct=b.cer_growth_pct,
                            )
                            for b in p.by_region
                        ],
                    )
                    for p in q.products
                ],
            )
            for q in company.quarters
        ],
    )


@strawberry.type
class Query:
    @strawberry.field(description="Every company in the dataset.")
    def companies(self) -> list[Company]:
        return [_to_graphql(c) for c in data.load_companies()]

    @strawberry.field(description="One company by id, or null if unknown.")
    def company(self, id: str = "sanofi") -> Company | None:
        found = data.find_company(id)
        return None if found is None else _to_graphql(found)


schema = strawberry.Schema(query=Query)
