# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-10-01  
**Run:** `singstat_priority_verified_run`  
**Generated at:** 2026-10-01T11:45:38+00:00  
**Analysis mode:** Live SoCLaaS Chat Completions tool-calling agent (qwen3.6:35b)  
**Data basis:** Latest downloaded vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 16 candidates and selected 5. soclaas_chat_completions_constrained_agent

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

**Source strategy:** SingStat first for every candidate; bounded request retries, independent candidates continue, transient failures rechecked; reviewed per-candidate backups enabled. Per-candidate attempts and actual routes are recorded in [source_routes.json](source_routes.json).

[完整指标池表：定义、纳入理由、官方来源和本次选择](indicator_pool.md) · [可搜索的表格预览](indicator_pool.html)

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Selected | Selected as an aggregate economic activity indicator. This series provides a quarterly view of real domestic output that may influence employment, incomes and housing confidence. The series is fully eligible and covers the full recent period, though it is not seasonally adjusted. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Selected | Selected as a labour-market condition measure for residents. A seasonally adjusted unemployment rate offers insight into workforce stability, which affects housing demand. The series is fully eligible with good coverage. It is excluded from the household income family to maintain theme diversity. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Selected | Selected as a quarterly income measure for employed residents. Mean gross employment income reflects purchasing power and borrowing capacity for the resident workforce. While the mean can be skewed by high earners, it complements the household median income by offering a workforce-level perspective. The series is fully eligible. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Selected | Selected as a financing cost indicator. The SORA benchmark provides monthly observations of the Singapore dollar interest rate environment, which directly affects mortgage affordability. While not an individual mortgage offer, it is a key reference for floating-rate loans. The series is highly eligible with extensive history. It is excluded from the inflation family because its primary role is financing cost rather than price-level tracking. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Resident Households (M810371:1) | population_demand | 2025 | 100 | Selected | Selected as a structural demand indicator measuring the number of resident households. Household counts serve as a proxy for potential housing demand and are distinct from population counts or new household formation. The series is fully eligible. It is excluded from the population demand family only in the sense of overlapping themes, but as a distinct identifier it captures a different demographic dimension. The annual frequency limits short-term timing precision. |
| Median Monthly Household Employment Income Including Employer CPF Contributions (M810361:5) | household_income | 2025 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Employment (Persons) As At Year End (M183111:7) | employment_level | 2025 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Total HDB Flats (M400751:1.1) | public_housing_supply | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |

## GDP In Chained (2015) Dollars

- **Series:** `M015661:1`; **Theme:** economic_activity
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M015661)
- **Definition:** Quarterly gross domestic product measured in chained 2015 Singapore dollars; a measure of real domestic economic activity.
- **Coverage:** Whole Singapore economy; million Singapore dollars at chained 2015 prices.
- **Unit:** Million Dollars; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 155,247.2 Million Dollars in 2026-Q2 (evidence `M015661:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 11/08/2026; **Retrieved:** 2026-10-01T11:47:04+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026-Q2 | 2025-Q2 | 5.9403 | % | M015661:1:year_on_year |

**Possible sales-market channel:** Higher real output may support jobs and incomes, potentially boosting housing purchasing capacity.

**Possible rental-market channel:** Stronger real economic activity may support employment and confidence, which could sustain rental demand.

**Possible lag:** Economic activity conditions may affect housing sales and rents over subsequent quarters.

**Limitations:** This series is not labelled seasonally adjusted, so year-on-year comparisons are prioritised. Advance estimates and historical data may be revised. GDP and housing may share common underlying causes.

Referenced evidence: `M015661:1:latest`, `M015661:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M015661_98fd049aa87c5bb9.json`; SHA-256 `138acbe058be5f2b1786287fa818e0efe86cebcd6877fbb79c9e832dc1093baf`.

Exact source row: `1` in table `M015661`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M015661:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 155,247.2 and 146,542.1.

</details>

## Resident Unemployment Rate, (SA)

- **Series:** `M182342:2`; **Theme:** labour_market
- **Source:** MINISTRY OF MANPOWER via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M182342)
- **Definition:** Resident unemployment rate at quarter-end, seasonally adjusted; residents are citizens and permanent residents.
- **Coverage:** Resident labour force, not the entire resident population or non-resident workforce.
- **Unit:** Per Cent; **Observation frequency:** Q; **Seasonal adjustment:** Seasonally Adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 2.9 Per Cent in 2026-Q2 (evidence `M182342:2:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 22/09/2026; **Retrieved:** 2026-10-01T11:47:04+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 0 | percentage points | M182342:2:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | 0.2 | percentage points | M182342:2:year_on_year |

**Possible sales-market channel:** A higher unemployment rate may weaken purchasing capacity and confidence, reducing housing demand.

**Possible rental-market channel:** A higher unemployment rate may weaken residents' ability to pay rents, though effects can vary by household circumstance.

**Possible lag:** Labour-market conditions may influence housing decisions with a lag as individuals adjust to workforce changes.

**Limitations:** The seasonally adjusted series is subject to annual revisions. It excludes non-residents and does not capture underemployment or job security.

Referenced evidence: `M182342:2:latest`, `M182342:2:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M182342_48b7788b41cef5e4.json`; SHA-256 `84b73c77a3fa5e42e0f44d882ba2c465d8d7d8e426020c3f02578f7976904f27`.

Exact source row: `2` in table `M182342`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M182342:2:previous_period`: `latest_value - base_value`; inputs 2.9 and 2.9.
- `M182342:2:year_on_year`: `latest_value - base_value`; inputs 2.9 and 2.7.

Source row note: The seasonally adjusted figures are derived using X-12 ARIMA to remove the seasonal influences in the data series.  The seasonally adjusted unemployment figures are subject to annual revisions when the latest set of seasonal factors is updated, taking into account observations for the latest available year.  Residents refer to Singapore citizens and Singapore Permanent Residents.

</details>

## Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents

- **Series:** `M184101:1`; **Theme:** household_income
- **Source:** MINISTRY OF MANPOWER via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M184101)
- **Definition:** Mean gross monthly employment income of employed residents, including employer CPF contributions and excluding bonus; employees' amounts are before employee CPF and income tax deductions.
- **Coverage:** Employed citizens and permanent residents excluding full-time National Servicemen; Singapore dollars per employed person.
- **Unit:** Dollars; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 6,605 Dollars in 2026-Q2 (evidence `M184101:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 31/08/2026; **Retrieved:** 2026-10-01T11:47:04+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2026-Q2 | 2025-Q2 | 3.3646 | % | M184101:1:year_on_year |

**Possible sales-market channel:** Higher employment income may improve borrowing capacity and purchasing power for home buyers.

**Possible rental-market channel:** Higher employment income may support rent affordability for resident workers.

**Possible lag:** Income changes may pass through to purchase and lease decisions over subsequent quarters.

**Limitations:** The measure includes employer CPF contributions and is not cash take-home pay. The mean can be skewed by high earners; composition of the workforce matters. Historical definition and coverage changes may limit comparability.

Referenced evidence: `M184101:1:latest`, `M184101:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M184101_fb465df65995a904.json`; SHA-256 `d8cbf8315336bd54bc69fc88739a236d44e8e9c0163deb5b497a83ea158917fe`.

Exact source row: `1` in table `M184101`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M184101:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 6,605 and 6,390.

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
- **Source table last updated:** 14/09/2026; **Retrieved:** 2026-10-01T11:47:05+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 5.09 | basis points | M700071:23:previous_period |
| year_on_year | 2026-08 | 2025-08 | -37.75 | basis points | M700071:23:year_on_year |

**Possible sales-market channel:** Higher benchmark rates may raise floating-rate financing costs and reduce borrowing capacity as mortgage terms reset.

**Possible rental-market channel:** Higher financing costs may shift tenure choices and affect landlord costs, though the net rental effect is ambiguous.

**Possible lag:** Pass-through to mortgage rates depends on pricing and reset dates, potentially affecting housing over subsequent months.

**Limitations:** This is a month-end benchmark snapshot. Individual mortgage spreads, fixed-rate loans and refinancing terms constrain pass-through. SORA changes alone cannot determine housing outcomes.

Referenced evidence: `M700071:23:latest`, `M700071:23:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M700071_5ec2ab86786f7bd2.json`; SHA-256 `844467d877f0fc311402be16f7fb1e606b894eb34185683c8a20f9039d4c70a2`.

Exact source row: `23` in table `M700071`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M700071:23:previous_period`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.1354.
- `M700071:23:year_on_year`: `(latest_value - base_value) * 100`; inputs 1.1863 and 1.5638.

</details>

## Resident Households

- **Series:** `M810371:1`; **Theme:** population_demand
- **Source:** SINGAPORE DEPARTMENT OF STATISTICS via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M810371)
- **Definition:** Annual number of resident households; household counts are distinct from population and are not the number of newly formed households.
- **Coverage:** Resident households. Source estimates combine Census of Population, General Household Survey and Comprehensive June Labour Force Survey; sampling variability and source changes apply.
- **Unit:** Number; **Observation frequency:** A; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Annual observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Individual observation publication dates are not confirmed.
- **Latest usable observation:** 1,487,100 Number in 2025 (evidence `M810371:1:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 30/06/2026; **Retrieved:** 2026-10-01T11:47:06+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2025 | 2024 | 1.6195 | % | M810371:1:year_on_year |

**Possible sales-market channel:** Household counts may better represent potential dwelling demand than population alone, subject to affordability constraints.

**Possible rental-market channel:** An increase in resident households may support rental demand depending on tenure choices and affordability.

**Possible lag:** Annual household formation provides structural context; short-term timing claims are limited.

**Limitations:** Household counts are not gross new formation. Census and survey years use different sources; period-end filtering is conservative. The annual frequency reduces short-term precision.

Referenced evidence: `M810371:1:latest`, `M810371:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M810371_8461ccdf2c645031.json`; SHA-256 `3b1c98d7f8191a8c4ab000444fe34c827a556ab416c85e2623154d79c458595d`.

Exact source row: `1` in table `M810371`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810371:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 1,487,100 and 1,463,400.

</details>

## Run limitations and reproducibility

- The model omitted 11 individual decision reasons; these exclusions are labelled as system explanations, not model reasoning.
- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
