"""Integrity tests for the transcribed sales dataset.

These assert properties of the *data*, not of the code: that the figures
satisfy the identities Sanofi's own reconciliation satisfies, that provenance
is present on every quarter, and that China is never double counted.

Product lines are each rounded to the nearest million in the source appendix,
so sums of many lines are checked against a small tolerance rather than for
exact equality. The tolerance is deliberately tight: it catches a transcription
error while accepting Sanofi's own rounding.
"""

from __future__ import annotations

import pytest

from api.data import REST_OF_WORLD, Company, Quarter, load_companies

#: Accumulated rounding across ~40 independently rounded product lines.
ROUNDING_TOLERANCE_EUR_M = 3

#: Company figures as published, used as fixtures for the FX/CER module too.
#: quarter id -> (net sales, fx effect, cer sales, cer growth, fx pp, reported)
PUBLISHED = {
    "Q1-2025": (9895, 98, 9797, 9.7, 1.1, 10.8),
    "Q2-2025": (9994, -384, 10378, 10.1, -4.1, 6.0),
    "Q3-2025": (12434, -578, 13012, 7.0, -4.7, 2.3),
    "Q1-2026": (10509, -733, 11242, 13.6, -7.4, 6.2),
}


@pytest.fixture(scope="module")
def sanofi() -> Company:
    companies = load_companies()
    return next(c for c in companies if c.id == "sanofi")


@pytest.fixture(scope="module")
def quarters(sanofi: Company) -> tuple[Quarter, ...]:
    return sanofi.quarters


def test_dataset_has_the_four_agreed_quarters(quarters: tuple[Quarter, ...]) -> None:
    assert [q.id for q in quarters] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q1-2026"]


def test_q4_2025_is_absent(quarters: tuple[Quarter, ...]) -> None:
    """Q4 is not issued standalone; it is folded into the FY2025 report."""
    assert "Q4-2025" not in {q.id for q in quarters}


@pytest.mark.parametrize("quarter_id", list(PUBLISHED))
def test_company_figures_match_the_press_release(
    sanofi: Company, quarter_id: str
) -> None:
    quarter = next(q for q in sanofi.quarters if q.id == quarter_id)
    c = quarter.company
    assert (
        c.net_sales_eur_m,
        c.fx_effect_eur_m,
        c.cer_sales_eur_m,
        c.cer_growth_pct,
        c.fx_impact_pp,
        c.reported_growth_pct,
    ) == PUBLISHED[quarter_id]


@pytest.mark.parametrize("quarter_id", list(PUBLISHED))
def test_cer_sales_identity(sanofi: Company, quarter_id: str) -> None:
    """cer_sales = net_sales - fx_effect, exactly, for every quarter."""
    c = next(q for q in sanofi.quarters if q.id == quarter_id).company
    assert c.cer_sales_eur_m == c.net_sales_eur_m - c.fx_effect_eur_m


@pytest.mark.parametrize("quarter_id", list(PUBLISHED))
def test_reported_growth_identity(sanofi: Company, quarter_id: str) -> None:
    """reported_growth = cer_growth + fx_impact_pp, to one decimal place."""
    c = next(q for q in sanofi.quarters if q.id == quarter_id).company
    assert c.reported_growth_pct == pytest.approx(
        c.cer_growth_pct + c.fx_impact_pp, abs=0.05
    )


def test_negative_fx_effect_means_cer_exceeds_net_sales(
    quarters: tuple[Quarter, ...],
) -> None:
    """The sign convention holds in both directions."""
    for quarter in quarters:
        c = quarter.company
        if c.fx_effect_eur_m < 0:
            assert c.cer_sales_eur_m > c.net_sales_eur_m
        elif c.fx_effect_eur_m > 0:
            assert c.cer_sales_eur_m < c.net_sales_eur_m


def test_top_level_regions_sum_to_company_net_sales(
    quarters: tuple[Quarter, ...],
) -> None:
    for quarter in quarters:
        top_level = [r for r in quarter.regions if r.subset_of is None]
        total = sum(r.net_sales_eur_m for r in top_level)
        assert total == pytest.approx(
            quarter.company.net_sales_eur_m, abs=ROUNDING_TOLERANCE_EUR_M
        ), f"{quarter.id}: regions sum to {total}"


def test_china_is_a_subset_of_rest_of_world(quarters: tuple[Quarter, ...]) -> None:
    for quarter in quarters:
        china = next(r for r in quarter.regions if r.region == "China")
        assert china.subset_of == REST_OF_WORLD


def test_china_is_excluded_from_the_regional_total(
    quarters: tuple[Quarter, ...],
) -> None:
    """Adding China to the top-level regions must overshoot the company total.

    This is the guard that matters: it fails if China is ever reclassified as
    a top-level region.
    """
    for quarter in quarters:
        china = next(r for r in quarter.regions if r.region == "China")
        naive_total = sum(r.net_sales_eur_m for r in quarter.regions)
        assert naive_total > quarter.company.net_sales_eur_m
        assert naive_total - china.net_sales_eur_m == pytest.approx(
            quarter.company.net_sales_eur_m, abs=ROUNDING_TOLERANCE_EUR_M
        )


def test_china_sits_within_rest_of_world(quarters: tuple[Quarter, ...]) -> None:
    for quarter in quarters:
        china = next(r for r in quarter.regions if r.region == "China")
        row = next(r for r in quarter.regions if r.region == REST_OF_WORLD)
        assert 0 < china.net_sales_eur_m < row.net_sales_eur_m


def test_products_sum_to_company_net_sales(quarters: tuple[Quarter, ...]) -> None:
    for quarter in quarters:
        total = sum(p.net_sales_eur_m for p in quarter.products)
        assert total == pytest.approx(
            quarter.company.net_sales_eur_m, abs=ROUNDING_TOLERANCE_EUR_M
        ), f"{quarter.id}: products sum to {total}"


def test_product_regional_splits_sum_to_regional_totals(
    quarters: tuple[Quarter, ...],
) -> None:
    """Each region's product lines reconcile with that region's published total."""
    for quarter in quarters:
        for region in (r for r in quarter.regions if r.subset_of is None):
            total = sum(
                b.net_sales_eur_m or 0
                for p in quarter.products
                for b in p.by_region
                if b.region == region.region
            )
            assert total == pytest.approx(
                region.net_sales_eur_m, abs=ROUNDING_TOLERANCE_EUR_M
            ), f"{quarter.id} {region.region}: products sum to {total}"


def test_therapeutic_area_subtotals_do_not_exceed_the_company_total(
    quarters: tuple[Quarter, ...],
) -> None:
    for quarter in quarters:
        areas: dict[str, int] = {}
        for product in quarter.products:
            areas[product.therapeutic_area] = (
                areas.get(product.therapeutic_area, 0) + product.net_sales_eur_m
            )
        assert areas, f"{quarter.id} has no therapeutic areas"
        for area, subtotal in areas.items():
            assert 0 < subtotal <= quarter.company.net_sales_eur_m, (
                f"{quarter.id} {area}"
            )


def test_every_quarter_carries_its_provenance(quarters: tuple[Quarter, ...]) -> None:
    for quarter in quarters:
        assert quarter.id
        assert quarter.label
        assert quarter.published_on
        assert quarter.comparative_period
        assert quarter.source_url.startswith("https://www.sanofi.com/")
        assert quarter.source_url.endswith(".pdf")


def test_source_urls_are_distinct_per_quarter(quarters: tuple[Quarter, ...]) -> None:
    urls = [q.source_url for q in quarters]
    assert len(set(urls)) == len(urls)


def test_products_are_never_empty_and_are_named(quarters: tuple[Quarter, ...]) -> None:
    for quarter in quarters:
        assert quarter.products, f"{quarter.id} has no products"
        for product in quarter.products:
            assert product.name
            assert product.therapeutic_area


def test_published_average_rates_cover_the_sensitivity_currencies(
    sanofi: Company,
) -> None:
    """Every currency with a disclosed sensitivity also has published rates."""
    sensitivity_currencies = {s.currency for s in sanofi.currency_sensitivities}
    for quarter in sanofi.quarters:
        rate_currencies = {r.currency for r in quarter.average_rates}
        assert sensitivity_currencies <= rate_currencies, quarter.id


def test_average_rates_are_positive_and_distinct_per_currency(
    quarters: tuple[Quarter, ...],
) -> None:
    for quarter in quarters:
        currencies = [r.currency for r in quarter.average_rates]
        assert len(set(currencies)) == len(currencies), quarter.id
        for rate in quarter.average_rates:
            assert rate.comparative_rate > 0
            assert rate.current_rate > 0


def test_q1_2026_usd_rate_matches_the_published_appendix(sanofi: Company) -> None:
    """Spot check against Appendix 7: the euro weakened from 1.053 to 1.171."""
    quarter = next(q for q in sanofi.quarters if q.id == "Q1-2026")
    usd = next(r for r in quarter.average_rates if r.currency == "USD")
    assert (usd.comparative_rate, usd.current_rate) == (1.053, 1.171)


def test_consecutive_quarter_comparatives_are_the_prior_year(
    quarters: tuple[Quarter, ...],
) -> None:
    """Growth is year-on-year, so the comparative is the same quarter last year."""
    for quarter in quarters:
        period, year = quarter.label.split(" ")
        assert quarter.comparative_period == f"{period} {int(year) - 1}"


def test_currency_exposure_shares_sum_to_about_one_hundred(sanofi: Company) -> None:
    total = sum(e.share_of_sales_pct for e in sanofi.currency_exposure)
    assert total == pytest.approx(100.0, abs=0.5)


def test_usd_is_the_largest_currency_exposure(sanofi: Company) -> None:
    """Over half of sales are in USD while reporting is in EUR.

    This mismatch is the reason the dashboard exists, so it is worth asserting.
    """
    entries = [e for e in sanofi.currency_exposure if e.currency != "Others"]
    largest = max(entries, key=lambda e: e.share_of_sales_pct)
    assert largest.currency == "USD"
    assert largest.share_of_sales_pct > 50


def test_currency_sensitivities_are_all_negative(sanofi: Company) -> None:
    """A stronger euro reduces net sales for every disclosed currency."""
    assert sanofi.currency_sensitivities
    for sensitivity in sanofi.currency_sensitivities:
        assert sensitivity.net_sales_impact_eur_m < 0
        assert sensitivity.variation


def test_company_level_metadata_is_present(sanofi: Company) -> None:
    assert sanofi.name == "Sanofi"
    assert sanofi.reporting_currency == "EUR"
    assert sanofi.segment == "Biopharma"
    assert sanofi.sensitivities_source_url.startswith("https://www.sanofi.com/")
    assert sanofi.exposure_source_url.startswith("https://www.sanofi.com/")
    assert sanofi.sensitivities_basis
    assert sanofi.exposure_basis


def test_dataset_is_keyed_by_company(sanofi: Company) -> None:
    """Shape allows a second reporter to be added as data, not as a migration."""
    assert sanofi.id == "sanofi"
    assert load_companies() is load_companies(), "dataset should be cached"


def test_aggregate_lines_are_flagged(quarters: tuple[Quarter, ...]) -> None:
    """Every quarter has an 'Others' line, and it is marked as an aggregate."""
    for quarter in quarters:
        others = next(p for p in quarter.products if p.name == "Others")
        assert others.is_aggregate
        dupixent = next(p for p in quarter.products if p.name == "Dupixent")
        assert not dupixent.is_aggregate


def test_named_products_alone_do_not_reach_the_company_total(
    quarters: tuple[Quarter, ...],
) -> None:
    """Aggregate lines are load-bearing: totals do not reconcile without them."""
    for quarter in quarters:
        named = sum(p.net_sales_eur_m for p in quarter.products if not p.is_aggregate)
        assert named < quarter.company.net_sales_eur_m
