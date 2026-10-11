"""Tests for the GraphQL schema and resolvers."""

from __future__ import annotations

from typing import Any

import pytest

from api.schema import schema


def run(query: str, **variables: Any) -> dict[str, Any]:
    """Execute a query, failing the test on any GraphQL error."""
    result = schema.execute_sync(query, variable_values=variables or None)
    assert result.errors is None, result.errors
    assert result.data is not None
    return result.data


def test_company_defaults_to_sanofi() -> None:
    data = run("{ company { id name reportingCurrency segment } }")
    assert data["company"] == {
        "id": "sanofi",
        "name": "Sanofi",
        "reportingCurrency": "EUR",
        "segment": "Biopharma",
    }


def test_unknown_company_returns_null_rather_than_erroring() -> None:
    data = run('{ company(id: "pfizer") { id } }')
    assert data["company"] is None


def test_companies_lists_every_reporter() -> None:
    data = run("{ companies { id } }")
    assert data["companies"] == [{"id": "sanofi"}]


def test_quarters_returns_the_four_quarters_in_order() -> None:
    data = run("{ company { quarters { id label } } }")
    assert data["company"]["quarters"] == [
        {"id": "Q1-2025", "label": "Q1 2025"},
        {"id": "Q2-2025", "label": "Q2 2025"},
        {"id": "Q3-2025", "label": "Q3 2025"},
        {"id": "Q1-2026", "label": "Q1 2026"},
    ]


def test_quarter_by_id_returns_the_published_figures() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            label
            sourceUrl
            comparativePeriod
            company {
              netSalesEurM fxEffectEurM cerSalesEurM
              cerGrowthPct fxImpactPp reportedGrowthPct
            }
        } } }
    """)
    quarter = data["company"]["quarter"]
    assert quarter["label"] == "Q1 2026"
    assert quarter["comparativePeriod"] == "Q1 2025"
    assert quarter["sourceUrl"].endswith(".pdf")
    assert quarter["company"] == {
        "netSalesEurM": 10509,
        "fxEffectEurM": -733,
        "cerSalesEurM": 11242,
        "cerGrowthPct": 13.6,
        "fxImpactPp": -7.4,
        "reportedGrowthPct": 6.2,
    }


def test_unknown_quarter_returns_null_rather_than_erroring() -> None:
    data = run('{ company { quarter(id: "Q4-2025") { id } } }')
    assert data["company"]["quarter"] is None


def test_latest_quarter_is_the_most_recently_published() -> None:
    data = run("{ company { latestQuarter { id publishedOn } } }")
    assert data["company"]["latestQuarter"] == {
        "id": "Q1-2026",
        "publishedOn": "2026-04-23",
    }


def test_regions_include_china_flagged_as_a_subset() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            regions { region netSalesEurM cerGrowthPct subsetOf }
        } } }
    """)
    regions = data["company"]["quarter"]["regions"]
    assert {r["region"] for r in regions} == {
        "United States",
        "Europe",
        "Rest of World",
        "China",
    }
    china = next(r for r in regions if r["region"] == "China")
    assert china == {
        "region": "China",
        "netSalesEurM": 649,
        "cerGrowthPct": -2.1,
        "subsetOf": "Rest of World",
    }


def test_top_level_regions_excludes_china() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            topLevelRegions { region netSalesEurM }
        } } }
    """)
    regions = data["company"]["quarter"]["topLevelRegions"]
    assert [r["region"] for r in regions] == [
        "United States",
        "Europe",
        "Rest of World",
    ]
    assert sum(r["netSalesEurM"] for r in regions) == 10509


def test_top_products_are_ranked_and_limited() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            topProducts(limit: 3) { name netSalesEurM therapeuticArea isAggregate }
        } } }
    """)
    products = data["company"]["quarter"]["topProducts"]
    assert products[0] == {
        "name": "Dupixent",
        "netSalesEurM": 4170,
        "therapeuticArea": "Immunology",
        "isAggregate": False,
    }
    sales = [p["netSalesEurM"] for p in products]
    assert sales == sorted(sales, reverse=True)
    assert len(products) == 3


def test_top_products_excludes_aggregate_lines_by_default() -> None:
    """'Others' is the second largest line in Q1 2026 but is not a product."""
    data = run("""
        { company { quarter(id: "Q1-2026") {
            topProducts(limit: 5) { name isAggregate }
        } } }
    """)
    products = data["company"]["quarter"]["topProducts"]
    assert not any(p["isAggregate"] for p in products)
    assert "Others" not in {p["name"] for p in products}


def test_top_products_can_include_aggregates_when_asked() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            topProducts(limit: 2, includeAggregates: true) { name }
        } } }
    """)
    names = [p["name"] for p in data["company"]["quarter"]["topProducts"]]
    assert names == ["Dupixent", "Others"]


def test_top_products_default_limit_is_ten() -> None:
    data = run('{ company { quarter(id: "Q1-2026") { topProducts { name } } } }')
    assert len(data["company"]["quarter"]["topProducts"]) == 10


def test_products_carry_both_cer_and_reported_growth() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            products { name cerGrowthPct reportedGrowthPct }
        } } }
    """)
    dupixent = next(
        p for p in data["company"]["quarter"]["products"] if p["name"] == "Dupixent"
    )
    assert dupixent["cerGrowthPct"] == 30.8
    assert dupixent["reportedGrowthPct"] == 19.8


def test_product_regional_split_allows_nulls_where_not_published() -> None:
    """ALTUVIIIO has no European sales; the field must be null, not zero."""
    data = run("""
        { company { quarter(id: "Q1-2026") {
            products { name byRegion { region netSalesEurM } }
        } } }
    """)
    altuviiio = next(
        p for p in data["company"]["quarter"]["products"] if p["name"] == "ALTUVIIIO"
    )
    europe = next(b for b in altuviiio["byRegion"] if b["region"] == "Europe")
    assert europe["netSalesEurM"] is None


def test_average_rates_expose_both_periods() -> None:
    data = run("""
        { company { quarter(id: "Q1-2026") {
            averageRates { currency comparativeRate currentRate }
        } } }
    """)
    rates = data["company"]["quarter"]["averageRates"]
    usd = next(r for r in rates if r["currency"] == "USD")
    assert usd == {"currency": "USD", "comparativeRate": 1.053, "currentRate": 1.171}


def test_currency_sensitivities_and_exposure_are_exposed_with_their_basis() -> None:
    data = run("""
        { company {
            sensitivitiesBasis
            sensitivitiesSourceUrl
            currencySensitivities { currency variation netSalesImpactEurM }
            exposureBasis
            currencyExposure { currency shareOfSalesPct }
        } }
    """)
    company = data["company"]
    usd = next(
        s for s in company["currencySensitivities"] if s["currency"] == "USD"
    )
    assert usd == {
        "currency": "USD",
        "variation": "+0.05 USD/EUR",
        "netSalesImpactEurM": -1069,
    }
    exposure = next(
        e for e in company["currencyExposure"] if e["currency"] == "USD"
    )
    assert exposure["shareOfSalesPct"] == 51.0
    assert company["sensitivitiesBasis"]
    assert company["exposureBasis"]
    assert company["sensitivitiesSourceUrl"].startswith("https://")


@pytest.mark.parametrize(
    "quarter_id,net_sales",
    [("Q1-2025", 9895), ("Q2-2025", 9994), ("Q3-2025", 12434), ("Q1-2026", 10509)],
)
def test_each_quarter_resolves_its_net_sales(quarter_id: str, net_sales: int) -> None:
    data = run(
        "query Q($id: String!) {"
        "  company { quarter(id: $id) { company { netSalesEurM } } }"
        "}",
        id=quarter_id,
    )
    assert data["company"]["quarter"]["company"]["netSalesEurM"] == net_sales


def test_schema_exposes_descriptions_for_the_fx_sign_convention() -> None:
    """The sign convention is easy to get wrong, so the schema documents it."""
    sdl = schema.as_str()
    assert "fxEffectEurM" in sdl
    assert "subsetOf" in sdl
    assert "Rest of World" in sdl
