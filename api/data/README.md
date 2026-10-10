# Sales data: sources and assumptions

All figures in `sales.json` are transcribed by hand from Sanofi's official
quarterly results press releases. **Nothing is invented, estimated, or rounded
to fill a gap.** Where a breakdown is not published, it is omitted and recorded
under [Known gaps](#known-gaps) below.

> `sales.json` is added in Phase 1. This file documents the sources and method
> that dataset follows.

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
not a separate region — it must not be added to the regional total.

## Currency exposure

Sanofi publishes currency exposure as a share of sales (Q1 2026, Appendix 7):

| Currency        | Share of sales |
| --------------- | -------------- |
| US Dollar       | 51.0%          |
| Euro            | 17.8%          |
| Chinese Yuan    | 5.9%           |
| Japanese Yen    | 2.8%           |
| Brazilian Real  | 2.4%           |
| Canadian Dollar | 1.4%           |
| Russian Ruble   | 1.3%           |

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
3. CER recalculation uses average rates for the comparative period. The exact
   internal rates Sanofi uses are not published, so ECB reference rates from
   the Frankfurter API stand in for them.

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
