# Sales data: sources and assumptions

All figures in `sales.json` are transcribed by hand from Sanofi's official
quarterly results press releases. **Nothing is invented, estimated, or rounded
to fill a gap.** Where a breakdown is not published, it is omitted and recorded
under [Known gaps](#known-gaps) below.

`sales.json` is keyed by company (`companies[]`), with Sanofi as the only
entry. Only companies that publish their own FX effect can be represented —
that figure is a non-IFRS measure each company defines itself, and it is not
available from any financial data API. Adding a second reporter is therefore a
transcription task, not a schema change.

## Sources

| Quarter | Published      | Press release                                                                                            |
| ------- | -------------- | -------------------------------------------------------------------------------------------------------- |
| Q1 2025 | 24 Apr 2025    | [PDF](https://www.sanofi.com/assets/dotcom/pressreleases/2025/2025-04-24-05-30-00-3067075-en.pdf)        |
| Q2 2025 | 31 Jul 2025    | [PDF](https://www.sanofi.com/assets/dotcom/pressreleases/2025/2025-07-31-05-30-00-3124660-en.pdf)        |
| Q3 2025 | 24 Oct 2025    | [PDF](https://www.sanofi.com/assets/dotcom/pressreleases/2025/2025-10-24-05-30-00-3172594-en.pdf)        |
| Q1 2026 | 23 Apr 2026    | [PDF](https://www.sanofi.com/assets/dotcom/pressreleases/2026/2026-04-23-05-30-00-3279572_EN.pdf)        |

Every record in `sales.json` carries its `quarter` and `sourceUrl`.

## Company-level figures

Taken from each release's sales commentary and the "Reconciliation of net sales
to company sales at CER" appendix.

| Quarter | Net sales | FX effect | CER sales | CER growth | FX impact | Reported growth |
| ------- | --------- | --------- | --------- | ---------- | --------- | --------------- |
| Q1 2025 | €9,895m   | +€98m     | €9,797m   | +9.7%      | +1.1pp    | +10.8%          |
| Q2 2025 | €9,994m   | −€384m    | €10,378m  | +10.1%     | −4.1pp    | +6.0%           |
| Q3 2025 | €12,434m  | −€578m    | €13,012m  | +7.0%      | −4.7pp    | +2.3%           |
| Q1 2026 | €10,509m  | −€733m    | €11,242m  | +13.6%     | −7.4pp    | +6.2%           |

These satisfy two identities, verified for all four quarters and used as test
fixtures for the FX/CER module:

```
CER sales       = net sales − FX effect
reported growth = CER growth + FX impact (pp)
```

Note the sign convention: a **negative** FX effect means currency movements
*reduced* reported EUR sales, so CER sales exceed net sales.

## Published average exchange rates

Each release gives the average rates used for the quarter **and** for the
comparative period (Appendix 7, "Currency average rates"). Since a CER
recalculation restates current-period sales at the comparative period's rates,
these are the rates the calculation needs, so they are stored per quarter in
`sales.json` under `averageRates`.

| Quarter | Comparative | €/$ | €/Yen | €/Yuan | €/Real | €/Ruble |
| ------- | ----------- | --- | ----- | ------ | ------ | ------- |
| Q1 2025 | Q1 2024 | 1.085 → 1.053 | 161.152 → 160.396 | 7.821 → 7.666 | 5.375 → 6.160 | 98.637 → 98.140 |
| Q2 2025 | Q2 2024 | 1.077 → 1.134 | 167.783 → 163.807 | 7.813 → 8.198 | 5.619 → 6.425 | 97.409 → 91.674 |
| Q3 2025 | Q3 2024 | 1.099 → 1.168 | 163.727 → 172.290 | 7.876 → 8.365 | 6.095 → 6.366 | 98.161 → 94.158 |
| Q1 2026 | Q1 2025 | 1.053 → 1.171 | 160.396 → 183.590 | 7.666 → 8.103 | 6.160 → 6.154 | 98.140 → 91.873 |

Using Sanofi's own published rates removes one of the approximations listed
below: the CER maths no longer has to substitute ECB reference rates for the
rates Sanofi actually applied. The Frankfurter API is still used for the
what-if scenario sliders, where the user is choosing a hypothetical rate and
no published figure exists.

## Sales by region

Reported in each release under "Sales by geography". Sanofi publishes net sales
in EUR and growth **at CER**; reported growth per region is derived from the
prior-year comparative where published.

| Quarter | United States    | Europe          | Rest of World   | _of which China_  |
| ------- | ---------------- | --------------- | --------------- | ----------------- |
| Q1 2025 | €4,657m (+15.4%) | €2,043m (+0.5%) | €3,195m (+8.4%) | €701m (−1.7%)     |
| Q2 2025 | €4,878m (+17.3%) | €2,101m (+3.0%) | €3,015m (+4.4%) | €687m (+1.8%)     |
| Q3 2025 | €6,838m (+11.1%) | €2,589m (+2.8%) | €3,007m (+1.9%) | €689m (+2.7%)     |
| Q1 2026 | €5,289m (+26.2%) | €2,163m (+5.9%) | €3,057m (+0.2%) | €649m (−2.1%)     |

Percentages are growth at CER. China is reported as a subset of Rest of World,
not a separate region — it must not be added to the regional total. In
`sales.json` it carries `subsetOf: "Rest of World"`, and the GraphQL schema
exposes a `topLevelRegions` field that filters it out so the values sum to the
company total.

## Products and therapeutic areas

Each release's Appendix 1 ("net sales by medicine/vaccine and geography") gives
every product line with total sales, growth **both** at CER and as reported,
and a United States / Europe / Rest of World split. All of it is transcribed:
148 product-quarter records across the four quarters.

**Sanofi publishes no business-unit breakdown.** All sales sit in a single
`Biopharma` segment, subdivided by therapeutic area: Immunology, Rare diseases,
Neurology, Oncology, Other main medicines, and Vaccines. That is the finest
published grouping above the product itself, so the dashboard's drill-down uses
therapeutic area where the original plan said "business unit".

Two Appendix 1 lines — `Others` and `Industrial Sales` — aggregate many
products rather than naming one. They are needed for the figures to reconcile
with the company total, so they are kept and flagged with `isAggregate`, and
excluded from "top products" rankings by default.

Because each line is rounded to the nearest million independently, summing
~40 of them lands within a few million of the published company total rather
than exactly on it (Q1 2026 reconciles exactly; the others are within €2m).
The test suite asserts a €3m tolerance, tight enough to catch a transcription
error while accepting Sanofi's rounding.

## Currency exposure

Sanofi publishes currency exposure as a share of sales (Q1 2026, Appendix 7):

| Currency          | Share of sales |
| ----------------- | -------------- |
| US Dollar         | 51.0%          |
| Euro              | 17.8%          |
| Chinese Yuan      | 5.9%           |
| Japanese Yen      | 2.8%           |
| Brazilian Real    | 2.4%           |
| Canadian Dollar   | 1.4%           |
| Russian Ruble     | 1.3%           |
| British Pound     | 1.3%           |
| Turkish Lira      | 1.2%           |
| Australian Dollar | 1.1%           |
| Others            | 13.8%          |

Over half of sales are denominated in US dollars while reporting is in euros.
That mismatch is why Sanofi has a large FX effect at all, and it is the reason
this dashboard exists.

It also publishes full-year sensitivities, used to calibrate the what-if
sliders rather than inventing elasticities:

| Currency       | Variation     | Net sales sensitivity |
| -------------- | ------------- | --------------------- |
| US Dollar      | +0.05 USD/EUR | −€1,069m              |
| Japanese Yen   | +5 JPY/EUR    | −€46m                 |
| Chinese Yuan   | +0.2 CNY/EUR  | −€60m                 |
| Brazilian Real | +0.4 BRL/EUR  | −€44m                 |

## The region-to-currency assumption

**This is the main approximation in the project and the app states it in the UI.**

Sanofi publishes FX impact at **company level only** — there is no per-region
currency effect in the releases. To show an FX waterfall per region, each
region is mapped to a currency or basket:

| Region        | Currency assumption                                |
| ------------- | -------------------------------------------------- |
| United States | USD                                                |
| Europe        | EUR (no FX effect by definition of the reporting currency) |
| China         | CNY                                                |
| Rest of World | Basket, weighted by published exposure (JPY, BRL, CAD, RUB, …) |

Consequences, stated plainly:

1. Regional sales are not purely single-currency. US sales may include
   non-USD transactions; European sales may include non-EUR currencies such as
   GBP or CHF.
2. Sanofi hedges currency exposure. Hedging is not visible in public data, so
   the modelled effect will not match the realised effect exactly.
3. ~~CER recalculation uses average rates for the comparative period. The
   exact internal rates Sanofi uses are not published, so ECB reference rates
   from the Frankfurter API stand in for them.~~ **No longer applies** — the
   releases publish the average rates for both periods (see above), so the
   calculation uses Sanofi's own figures.

The **validation view** exists because of this. It compares the approximated
CER growth with Sanofi's published CER growth and displays the difference, so
the size of the approximation is visible instead of hidden.

## Known gaps

- **FX effect per region** — not published. Approximated as described above.
- **Sales by currency** — not published; only exposure percentages are.
- **Q4 2025 standalone** — not issued as a separate quarterly release; Q4 is
  reported within the FY2025 results. Excluded to keep quarters comparable.
- **Reported (non-CER) growth per region** — not given directly in every
  release; derived from prior-year comparatives only where published, otherwise
  omitted.
- **Hedging** — not disclosed at a level usable here.
- **Currency sensitivities** — published as full-year figures, not quarterly.
  Used as directional calibration, not as exact quarterly values.
- **Sales by business unit** — not published. Sanofi reports one Biopharma
  segment; therapeutic area is the finest grouping available.
- **Sales in original currencies** — not published. Only EUR figures and
  exposure percentages are given, so the absolute amount earned in each
  currency cannot be derived.
