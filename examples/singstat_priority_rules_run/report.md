# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-10-01  
**Run:** `singstat_priority_rules_run`  
**Generated at:** 2026-10-01T11:49:00+00:00  
**Analysis mode:** Deterministic rules; reviewed qualitative templates, no model call  
**Data basis:** Verified saved source snapshot from singstat_priority_verified_run, captured from 2026-10-01T11:47:03+00:00; original retrieval timestamps are preserved. No new source refresh was performed. Saved captured vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 16 candidates and selected 5. Deterministic data-quality and economic-family diversity selection. Family is metadata.selection_family when specified, otherwise metadata.theme. Exclude ineligible data; sort by quality score descending then id ascending; first select the best candidate per family, then fill remaining capacity by score. Never fill capacity with ineligible data. Scores measure usability and do not establish causal or predictive value; no target-based predictive validation is performed.

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

**Source strategy:** Verified saved snapshot; no new retrieval. Per-candidate attempts and actual routes are recorded in [source_routes.json](source_routes.json).

[完整指标池表：定义、纳入理由、官方来源和本次选择](indicator_pool.md) · [可搜索的表格预览](indicator_pool.html)

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Selected | Selected for economic-family coverage (population_demand): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: population_demand. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: economic_activity. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: labour_market. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: household_income. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: household_income. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: financing_cost. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_credit. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: housing_supply. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Selected | Selected for economic-family coverage (inflation): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Resident Households (M810371:1) | population_demand | 2025 | 100 | Excluded | Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: population_demand. |
| Median Monthly Household Employment Income Including Employer CPF Contributions (M810361:5) | household_income | 2025 | 100 | Selected | Selected for economic-family coverage (household_income): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Employment (Persons) As At Year End (M183111:7) | employment_level | 2025 | 100 | Selected | Selected for economic-family coverage (labour_market): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |
| Total HDB Flats (M400751:1.1) | public_housing_supply | 2026 | 100 | Selected | Selected for economic-family coverage (housing_supply): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified. |

## Employment (Persons) As At Year End

- **Series:** `M183111:7`; **Theme:** employment_level
- **Source:** MINISTRY OF MANPOWER via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M183111)
- **Definition:** Total persons in employment as at year-end, expressed in thousands; includes migrant domestic workers and excludes persons serving two-year full-time national service.
- **Coverage:** Resident and non-resident employees plus self-employed persons. MOM administrative-record coverage excludes two-year full-time national servicemen; the current MOM summary identifies the matching total as including migrant domestic workers. SingStat row footnote confirms administrative records plus Labour Force Survey estimates for the self-employed.
- **Unit:** Thousand; **Observation frequency:** A; **Seasonal adjustment:** Non-seasonally Adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Individual observation publication dates are not confirmed.
- **Latest usable observation:** 4,117 Thousand in 2025 (evidence `M183111:7:latest`)
- **Observation reference date:** 2025-12-31
- **Source table last updated:** 31/07/2026; **Retrieved:** 2026-10-01T11:47:07+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2025 | 2024 | 1.7498 | % | M183111:7:year_on_year |

**Possible sales-market channel:** A larger employment base may support aggregate earned income and housing purchasing capacity.

**Possible rental-market channel:** Employment expansion may support work-related housing and rental demand.

**Possible lag:** Annual year-end employment context; housing responses need not be simultaneous.

**Limitations:** Counts employed persons, not vacancies, new hires or the unemployment rate. Includes migrant domestic workers and other workers whose accommodation need is not an ordinary separate rental unit. Employment and housing may share common causes; not a residents-only series.

Referenced evidence: `M183111:7:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M183111_78ebddbf3477131c.json`; SHA-256 `091816d24a8931e0b39195330d1c3b00fca60057cff5755fadcdbd6ec53487cd`.

Exact source row: `7` in table `M183111`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M183111:7:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 4,117 and 4,046.2.

Source row note: Data are compiled primarily from administrative records, wtih the self-employed component estimated from the Labour Force Survey.

</details>

## Total HDB Flats

- **Series:** `M400751:1.1`; **Theme:** public_housing_supply
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M400751)
- **Definition:** Total HDB flats as at end-June of each year, including non-privatised Housing and Urban Development Corporation flats.
- **Coverage:** Public-housing dwelling stock; not annual completions, BTO launches, resale transactions or flats available for rent.
- **Unit:** Number; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Individual observation publication dates are not confirmed.
- **Latest usable observation:** 1,177,601 Number in 2026 (evidence `M400751:1.1:latest`)
- **Observation reference date:** 2026-06-30
- **Source table last updated:** 25/09/2026; **Retrieved:** 2026-10-01T11:47:07+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026 | 2025 | 1.4705 | % | M400751:1.1:year_on_year |

**Possible sales-market channel:** The public-housing stock adds supply context not represented by private residential stock and may influence tenure and purchase choices.

**Possible rental-market channel:** Public-housing supply can affect tenure choices and rental alternatives subject to eligibility and rental rules.

**Possible lag:** Annual supply stock; allocations, completion and occupation timing can differ.

**Limitations:** Stock is not new supply or vacancies and includes non-privatised HUDC flats. Public and private markets differ in eligibility and policy; aggregate stock alone does not predict prices or rents.

Referenced evidence: `M400751:1.1:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.
- Data warning: Used source-backed observation dates within the period for 27 observations; other observations use period-end cutoffs.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M400751_c10997a05cec390f.json`; SHA-256 `ae44af016d20a58cd79503fe3d95d1e18e17f10218aae45b76afe211b8c363bf`.

Exact source row: `1.1` in table `M400751`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M400751:1.1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 1,177,601 and 1,160,535.

Source row note: Includes non-privatised Housing and Urban Development Corporation flats.

</details>

## Resident Population

- **Series:** `M810001:2`; **Theme:** population_demand
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M810001)
- **Definition:** Singapore citizens and permanent residents as at end-June; from 2003 excludes residents continuously overseas for at least 12 months at the reference date.
- **Coverage:** Singapore resident population, not number of households or homebuyers.
- **Unit:** Number; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 4,231,524 Number in 2026 (evidence `M810001:2:latest`)
- **Observation reference date:** 2026-06-30
- **Source table last updated:** 25/09/2026; **Retrieved:** 2026-10-01T11:47:03+00:00

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

Raw response: `raw/tabledata_M810001_111a5f764bb0c97b.json`; SHA-256 `998bd3587b86d8d74e329bcc6a6a5225966482a689d42eec3a165e2f3452d6d2`.

Exact source row: `2` in table `M810001`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810001:2:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 4,231,524 and 4,204,515.

Source row note: Data are as at end-June.  Data prior to 1990 are based on de facto concept (i.e. the person is present in the country at the reference period), while data from 1990 onwards are based on de jure concept (i.e. the person's place of usual residence).  Data from 2003 onwards exclude residents who are overseas for a continuous period of 12 months or longer as at the reference period.

</details>

## Median Monthly Household Employment Income Including Employer CPF Contributions

- **Series:** `M810361:5`; **Theme:** household_income
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M810361)
- **Definition:** Median nominal monthly household employment income among resident employed households, including employer CPF contributions and one-twelfth of annual bonus, before Government transfers and taxes.
- **Coverage:** Households whose reference person is a citizen or permanent resident and with at least one employed member. Income sums employment and business income of employed household members, excluding live-in domestic workers.
- **Unit:** Dollar; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Individual observation publication dates are not confirmed.
- **Latest usable observation:** 12,027 Dollar in 2025 (evidence `M810361:5:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 09/02/2026; **Retrieved:** 2026-10-01T11:47:07+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2025 | 2024 | 6.3019 | % | M810361:5:year_on_year |

**Possible sales-market channel:** Median household employment income may describe typical household purchasing capacity more directly than mean income per employed person.

**Possible rental-market channel:** Median household income may contextualise household rent affordability.

**Possible lag:** Annual affordability context; income and financing decisions can adjust over subsequent quarters.

**Limitations:** Not income per household member or an individual wage. Excludes households with no employed person; includes employer CPF and annual bonus allocation, unlike the existing bonus-excluding quarterly individual mean. Nominal and not take-home income.

Referenced evidence: `M810361:5:latest`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M810361_ace929ea782b332d.json`; SHA-256 `64b079f81758a381e25fe6bc001bf4ee5057f00f4d86c542b8fbbfa85313b231`.

Exact source row: `5` in table `M810361`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810361:5:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 12,027 and 11,314.

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
- **Source table last updated:** 23/09/2026; **Retrieved:** 2026-10-01T11:47:06+00:00

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

Raw response: `raw/tabledata_M213751_62f62cd25bf5df72.json`; SHA-256 `28aec21bd4c894fbc1df63dd140903d8342e8e064bd3ad8e9997aa02a58c9669`.

Exact source row: `1` in table `M213751`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M213751:1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 103.334 and 102.696.
- `M213751:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 103.334 and 100.963.

</details>

## Run limitations and reproducibility

- Verified saved source snapshot from singstat_priority_verified_run, captured from 2026-10-01T11:47:03+00:00; original retrieval timestamps are preserved. No new source refresh was performed.
- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
