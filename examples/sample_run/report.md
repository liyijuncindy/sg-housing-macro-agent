# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-09-30  
**Run:** `sample_run`  
**Generated at:** 2026-09-30T16:48:33+00:00  
**Analysis mode:** Deterministic rules; reviewed qualitative templates, no model call  
**Data basis:** Latest downloaded vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 12 candidates and selected 5. Deterministic data-quality and economic-family diversity selection. Family is metadata.selection_family when specified, otherwise metadata.theme. Exclude ineligible data; sort by quality score descending then id ascending; first select the best candidate per family, then fill remaining capacity by score. Never fill capacity with ineligible data. Scores measure usability and do not establish causal or predictive value; no target-based predictive validation is performed.

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Selected | Selected for economic-family coverage (population_demand): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: population_demand. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Selected | Selected for economic-family coverage (economic_activity): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: labour_market. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: household_income. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: household_income. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Selected | Selected for economic-family coverage (financing_cost): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Selected | Selected for economic-family coverage (housing_credit): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Selected | Selected for economic-family coverage (inflation): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |

## Resident Population

- **Series:** `M810001:2`; **Theme:** population_demand
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M810001)
- **Definition:** Singapore citizens and permanent residents as at end-June; from 2003 excludes residents continuously overseas for at least 12 months at the reference date.
- **Coverage:** Singapore resident population, not number of households or homebuyers.
- **Unit:** Number; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 4,231,524 Number in 2026 (evidence `M810001:2:latest`)
- **Observation reference date:** 2026-06-30
- **Source table last updated:** 25/09/2026; **Retrieved:** 2026-09-30T16:49:33+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026 | 2025 | 0.6424 | % | M810001:2:year_on_year |

**Possible sales-market channel:** A larger resident population may support owner-occupier demand when household formation and purchasing capacity also increase.

**Possible rental-market channel:** Population growth may support rental demand, conditional on household formation and tenure choices.

**Possible lag:** Annual demand context; the effect may develop over multiple quarters.

**Limitations:** Population is not household formation; pre-1990 population concepts and the 2003 coverage change limit long-run comparability. Historical observations may be revised.

Referenced evidence: `M810001:2:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
- Data warning: Used source-backed observation dates within the period for 48 observations; other observations use period-end cutoffs.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M810001_111a5f764bb0c97b.json`; SHA-256 `888cc3db49eecf57aa7fa057b11b3b8c606d88f7b7eade838be416516a8730de`.

Exact source row: `2` in table `M810001`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810001:2:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 4,231,524 and 4,204,515.

Source row note: Data are as at end-June.  Data prior to 1990 are based on de facto concept (i.e. the person is present in the country at the reference period), while data from 1990 onwards are based on de jure concept (i.e. the person's place of usual residence).  Data from 2003 onwards exclude residents who are overseas for a continuous period of 12 months or longer as at the reference period.

</details>

## All Items

- **Series:** `M213751:1`; **Theme:** inflation
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M213751)
- **Definition:** All-items Consumer Price Index, 2024 = 100, based on the official household expenditure weighting pattern.
- **Coverage:** Singapore consumer prices; index, not residential property sale prices.
- **Unit:** Index; **Observation frequency:** M; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Monthly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 103.334 Index in 2026-08 (evidence `M213751:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 23/09/2026; **Retrieved:** 2026-09-30T16:49:36+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 0.6213 | % | M213751:1:previous_period |
| year_on_year | 2026-08 | 2025-08 | 2.3484 | % | M213751:1:year_on_year |

**Possible sales-market channel:** Inflation affects real purchasing power and building or financing conditions, but its net association with home values is ambiguous.

**Possible rental-market channel:** Inflation affects household budgets and landlords' costs, with an ambiguous net effect on rent growth.

**Possible lag:** Monthly cost-of-living context; effects can be contemporaneous or lagged.

**Limitations:** CPI includes housing-related components, so its relationship with rents can partly reflect overlap. It is not a construction-cost index, house-price index or independent causal predictor.

Referenced evidence: `M213751:1:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M213751_62f62cd25bf5df72.json`; SHA-256 `12c460c3f71a1a1e505894ec77d33ed9c9b289530e31965f69ffcde8c03cd114`.

Exact source row: `1` in table `M213751`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M213751:1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 103.334 and 102.696.
- `M213751:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 103.334 and 100.963.

</details>

## Compounded Singapore Overnight Rate Average (SORA) - 3 Month

- **Series:** `M700071:23`; **Theme:** financing_cost
- **Source:** MONETARY AUTHORITY OF SINGAPORE via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M700071)
- **Definition:** Three-month compounded Singapore Overnight Rate Average (SORA), observed at month-end and expressed as an annual percentage rate.
- **Coverage:** Singapore-dollar benchmark interest rate; not an individual mortgage offer.
- **Unit:** Per Cent Per Annum; **Observation frequency:** M; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Monthly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 1.1863 Per Cent Per Annum in 2026-08 (evidence `M700071:23:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 14/09/2026; **Retrieved:** 2026-09-30T16:49:35+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 5.09 | basis points | M700071:23:previous_period |
| year_on_year | 2026-08 | 2025-08 | -37.75 | basis points | M700071:23:year_on_year |

**Possible sales-market channel:** Higher benchmark rates may raise floating-rate financing costs and reduce borrowing capacity as mortgage rates reset.

**Possible rental-market channel:** Higher ownership financing costs may shift tenure choices and landlords' costs; the net rental effect is ambiguous.

**Possible lag:** Pass-through depends on mortgage pricing, reset dates and fixed-rate periods, often over subsequent months.

**Limitations:** Month-end snapshot, not a monthly average. Mortgage spreads, fixed-rate loans, refinancing terms and policy constrain pass-through; SORA changes alone cannot determine housing prices.

Referenced evidence: `M700071:23:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M700071_5ec2ab86786f7bd2.json`; SHA-256 `77fc485912f5d154d7864b59674a24e2c1cc6ed8a62230c1deb7df1cd8de52a5`.

Exact source row: `23` in table `M700071`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M700071:23:previous_period`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.1354.
- `M700071:23:year_on_year`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.5638.

</details>

## Consumer Loans - Housing And Bridging Loans

- **Series:** `M701091:1.2.1`; **Theme:** housing_credit
- **Source:** MONETARY AUTHORITY OF SINGAPORE via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M701091)
- **Definition:** Commercial-bank consumer housing and bridging loans to residents outstanding at month-end.
- **Coverage:** Commercial-bank lending stock to residents; million Singapore dollars, not new monthly mortgage approvals.
- **Unit:** Million Dollars; **Observation frequency:** M; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Monthly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 256,563.5 Million Dollars in 2026-08 (evidence `M701091:1.2.1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 30/09/2026; **Retrieved:** 2026-09-30T16:49:35+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 0.7422 | % | M701091:1.2.1:previous_period |
| year_on_year | 2026-08 | 2025-08 | 7.2804 | % | M701091:1.2.1:year_on_year |

**Possible sales-market channel:** Expanding housing credit may accompany financed housing demand, but it can also respond to higher prices.

**Possible rental-market channel:** Credit conditions may affect ownership-versus-renting decisions; the rental relationship is indirect.

**Possible lag:** Credit stocks adjust gradually and may lag transactions.

**Limitations:** This is outstanding stock, not credit availability or origination flow; repayments also affect it. Revised reporting starts July 2021 following changes to MAS Notices 610 and 1003.

Referenced evidence: `M701091:1.2.1:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M701091_11d6417c6fe41133.json`; SHA-256 `f807742a147f6371df8587149a337395147ca3ff82d44ba00992dd4d8aba68f1`.

Exact source row: `1.2.1` in table `M701091`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M701091:1.2.1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 256,563.5 and 254,673.3.
- `M701091:1.2.1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 256,563.5 and 239,152.3.

</details>

## GDP In Chained (2015) Dollars

- **Series:** `M015661:1`; **Theme:** economic_activity
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M015661)
- **Definition:** Quarterly gross domestic product measured in chained 2015 Singapore dollars; a measure of real domestic economic activity.
- **Coverage:** Whole Singapore economy; million Singapore dollars at chained 2015 prices.
- **Unit:** Million Dollars; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 155,247.2 Million Dollars in 2026-Q2 (evidence `M015661:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 11/08/2026; **Retrieved:** 2026-09-30T16:49:34+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026-Q2 | 2025-Q2 | 5.9403 | % | M015661:1:year_on_year |

**Possible sales-market channel:** Stronger real activity may support jobs, incomes and confidence, which can support purchasing demand.

**Possible rental-market channel:** Stronger activity may support employment-linked rental demand.

**Possible lag:** Economic conditions may affect housing over several quarters.

**Limitations:** This series is not labelled seasonally adjusted: prioritise year-on-year comparisons. GDP and housing may share common causes; advance estimates and history can be revised.

Referenced evidence: `M015661:1:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M015661_98fd049aa87c5bb9.json`; SHA-256 `75ee0ac536d3a39fc6f75daec337db6ad5490bef29e97a666af54a1c11adde04`.

Exact source row: `1` in table `M015661`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M015661:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 155,247.2 and 146,542.1.

</details>

## Run limitations and reproducibility

- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
