# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-09-30  
**Run:** `soclaas_verified_run`  
**Generated at:** 2026-10-01T08:43:30+00:00  
**Analysis mode:** Live SoCLaaS Chat Completions tool-calling agent (qwen3.6:35b)  
**Data basis:** Verified saved source snapshot from sample_run, captured from 2026-09-30T16:49:33+00:00; original retrieval timestamps are preserved. No new source refresh was performed. Saved captured vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 12 candidates and selected 5. soclaas_chat_completions_constrained_agent

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Selected | Rental demand from non-resident population, capturing tenant-side dynamics. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Selected | Aggregatemean purchasing resources and affordability conditions. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Selected | Financing costs and borrowing capacity for purchasers. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Selected | Current completed supply and its interaction with absorption. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Selected | Future supply expectations and medium-term balance between demand and completions. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |

## Personal Disposable Income (Nominal)

- **Series:** `M016081:1`; **Theme:** household_income
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M016081)
- **Definition:** Quarterly aggregate personal disposable income at current prices.
- **Coverage:** Singapore aggregate nominal personal disposable income; million Singapore dollars, not median household income.
- **Unit:** Million Dollars; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 94,423.4 Million Dollars in 2026-Q2 (evidence `M016081:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 25/08/2026; **Retrieved:** 2026-09-30T16:49:34+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026-Q2 | 2025-Q2 | 6.8838 | % | M016081:1:year_on_year |

**Possible sales-market channel:** Higher aggregate disposable income may increase the resources available for housing purchases.

**Possible rental-market channel:** Higher aggregate disposable income may support rental spending.

**Possible lag:** Quarterly affordability context; decisions may adjust with a lag.

**Limitations:** Nominal aggregate growth also reflects inflation and population change; it is not income per household. This series is not labelled seasonally adjusted.

Referenced evidence: `M016081:1:latest`, `M016081:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M016081_3de81f4c4307fd66.json`; SHA-256 `448cba08c23cc66edf328c25323733a2be3707585da3e5ed6e09a130560d3f4c`.

Exact source row: `1` in table `M016081`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M016081:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 94,423.4 and 88,342.1.

</details>

## Total Non-Landed Properties

- **Series:** `M400391:2`; **Theme:** future_supply
- **Source:** URBAN REDEVELOPMENT AUTHORITY via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M400391)
- **Definition:** Total non-landed private residential units in the pipeline at quarter-end across development statuses.
- **Coverage:** Non-landed private residential pipeline; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.
- **Unit:** Number Of Units; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 51,677 Number Of Units in 2026-Q2 (evidence `M400391:2:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 24/07/2026; **Retrieved:** 2026-09-30T16:49:36+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 7.412 | % | M400391:2:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | 6.6077 | % | M400391:2:year_on_year |

**Possible sales-market channel:** A larger prospective pipeline may ease expected future supply constraints.

**Possible rental-market channel:** Future completions may expand potential rental supply.

**Possible lag:** Medium to long term; timing varies across under-construction and planned developments.

**Limitations:** The pipeline is not completed housing or a completion forecast. Timing, cancellations and development stages vary; landed housing is excluded from this row.

Referenced evidence: `M400391:2:latest`, `M400391:2:previous_period`, `M400391:2:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M400391_fb25f7621ca819ff.json`; SHA-256 `eea996c10aff041ed6a245a2a80fe0a0588c278f7c9fd4045bd2f8206a3d7c59`.

Exact source row: `2` in table `M400391`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M400391:2:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 51,677 and 48,111.
- `M400391:2:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 51,677 and 48,474.

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

Referenced evidence: `M700071:23:latest`, `M700071:23:previous_period`, `M700071:23:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M700071_5ec2ab86786f7bd2.json`; SHA-256 `77fc485912f5d154d7864b59674a24e2c1cc6ed8a62230c1deb7df1cd8de52a5`.

Exact source row: `23` in table `M700071`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M700071:23:previous_period`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.1354.
- `M700071:23:year_on_year`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.5638.

</details>

## Non-Resident Population

- **Series:** `M810001:5`; **Theme:** population_demand
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M810001)
- **Definition:** Foreigners working, studying or living in Singapore without permanent residence, excluding tourists and short-term visitors, as at end-June.
- **Coverage:** Singapore non-resident population; housing needs include arrangements beyond private residential rentals.
- **Unit:** Number; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 1,976,999 Number in 2026 (evidence `M810001:5:latest`)
- **Observation reference date:** 2026-06-30
- **Source table last updated:** 25/09/2026; **Retrieved:** 2026-09-30T16:49:33+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026 | 2025 | 3.6891 | % | M810001:5:year_on_year |

**Possible sales-market channel:** An increase may support housing demand indirectly, but tenure preferences and purchase restrictions affect the link to sales.

**Possible rental-market channel:** A larger non-resident population may support rental demand where residents seek ordinary residential accommodation.

**Possible lag:** Annual demand context; moves and lease renewals may transmit over subsequent quarters.

**Limitations:** Does not identify income, visa category, dormitory residence, household size or dwelling tenure. Population alone is not a rental-demand forecast.

Referenced evidence: `M810001:5:latest`, `M810001:5:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
- Data warning: Used source-backed observation dates within the period for 48 observations; other observations use period-end cutoffs.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M810001_495ed32846bcfef1.json`; SHA-256 `3032e00afc9d10c63b3a055ab8fabbce54299f812cb600deb66de3b65f46ae02`.

Exact source row: `5` in table `M810001`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810001:5:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 1,976,999 and 1,906,660.

Source row note: Data are as at end-June.  Non-resident population comprises foreigners who were working, studying or living in Singapore but not granted permanent residence, excluding tourists and short-term visitors.

</details>

## All Types Private Residential Properties Available

- **Series:** `M400841:1`; **Theme:** completed_supply
- **Source:** URBAN REDEVELOPMENT AUTHORITY via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M400841)
- **Definition:** Completed private residential units at quarter-end with a Temporary Occupation Permit or Certificate of Statutory Completion; this is the housing stock labelled available by URA.
- **Coverage:** All landed and non-landed private residential units; excludes hostels, HDB flats, tenement houses, parsonages and Executive Condominiums.
- **Unit:** Number Of Units; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 424,581 Number Of Units in 2026-Q2 (evidence `M400841:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 24/07/2026; **Retrieved:** 2026-09-30T16:49:35+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 0.0981 | % | M400841:1:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | 1.0565 | % | M400841:1:year_on_year |

**Possible sales-market channel:** Growth in completed stock may ease supply constraints relative to demand.

**Possible rental-market channel:** Additional completed homes may increase potential rental supply.

**Possible lag:** Completed stock is available in the current period; absorption may take subsequent quarters.

**Limitations:** Available denotes total completed stock, not units actively listed for sale or rent. Historical definition and coverage changes may limit comparability.

Referenced evidence: `M400841:1:latest`, `M400841:1:previous_period`, `M400841:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M400841_9cbe20a8bfdb6540.json`; SHA-256 `97273c9aeaac6810ccb00fb908640d6623ac5cb583e99dd8426cc162018bc94e`.

Exact source row: `1` in table `M400841`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M400841:1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 424,581 and 424,165.
- `M400841:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 424,581 and 420,142.

</details>

## Run limitations and reproducibility

- Verified saved source snapshot from sample_run, captured from 2026-09-30T16:49:33+00:00; original retrieval timestamps are preserved. No new source refresh was performed.
- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
