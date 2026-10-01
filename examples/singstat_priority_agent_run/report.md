# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-10-01  
**Run:** `singstat_priority_agent_run`  
**Generated at:** 2026-10-01T11:37:39+00:00  
**Analysis mode:** Live SoCLaaS Chat Completions tool-calling agent (qwen3.6:35b)  
**Data basis:** Latest downloaded vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 16 candidates and selected 1. soclaas_chat_completions_constrained_agent

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

**Source strategy:** SingStat first for every candidate; bounded request retries, independent candidates continue, transient failures rechecked before reviewed backups. Per-candidate attempts and actual routes are recorded in [source_routes.json](source_routes.json).

[完整指标池表：定义、纳入理由、官方来源和本次选择](indicator_pool.md) · [可搜索的表格预览](indicator_pool.html)

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Selected | The seasonally adjusted resident unemployment rate is eligible and timely. Unemployment directly reflects current labour-market stress, which may weaken resident purchasing capacity and rental affordability. Its seasonally adjusted nature and high completeness justify selection. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Resident Households (M810371:1) | population_demand | 2025 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Median Monthly Household Employment Income Including Employer CPF Contributions (M810361:5) | household_income | 2025 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Employment (Persons) As At Year End (M183111:7) | employment_level | 2025 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |
| Total HDB Flats (M400751:1.1) | public_housing_supply | 2026 | 100 | Excluded | System exclusion: eligible candidate was not selected in the model's submitted subset; the model did not provide an individual exclusion reason. |

## Resident Unemployment Rate, (SA)

- **Series:** `M182342:2`; **Theme:** labour_market
- **Source:** MINISTRY OF MANPOWER via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M182342)
- **Definition:** Resident unemployment rate at quarter-end, seasonally adjusted; residents are citizens and permanent residents.
- **Coverage:** Resident labour force, not the entire resident population or non-resident workforce.
- **Unit:** Per Cent; **Observation frequency:** Q; **Seasonal adjustment:** Seasonally Adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 2.9 Per Cent in 2026-Q2 (evidence `M182342:2:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 22/09/2026; **Retrieved:** 2026-10-01T11:39:13+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 0 | percentage points | M182342:2:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | 0.2 | percentage points | M182342:2:year_on_year |

**Possible sales-market channel:** Elevated resident unemployment may constrain purchasing capacity and buyer confidence, potentially slowing sales transactions or reducing sales price growth.

**Possible rental-market channel:** A higher resident unemployment rate may weaken residents' ability to pay rents, potentially reducing rental demand and dampening rent growth.

**Possible lag:** Current labour-market conditions may transmit to housing over subsequent quarters as tenants and buyers adjust to employment security.

**Limitations:** The seasonally adjusted series is revised annually. It excludes non-residents and does not capture job losses among residents who remain classified as employed, underemployment, or changes in work-from-home patterns that affect housing space requirements.

Referenced evidence: `M182342:2:latest`, `M182342:2:previous_period`, `M182342:2:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M182342_48b7788b41cef5e4.json`; SHA-256 `84b73c77a3fa5e42e0f44d882ba2c465d8d7d8e426020c3f02578f7976904f27`.

Exact source row: `2` in table `M182342`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M182342:2:previous_period`: `latest_value - base_value`; inputs 2.9 and 2.9.
- `M182342:2:year_on_year`: `latest_value - base_value`; inputs 2.9 and 2.7.

Source row note: The seasonally adjusted figures are derived using X-12 ARIMA to remove the seasonal influences in the data series.  The seasonally adjusted unemployment figures are subject to annual revisions when the latest set of seasonal factors is updated, taking into account observations for the latest available year.  Residents refer to Singapore citizens and Singapore Permanent Residents.

</details>

## Run limitations and reproducibility

- Selected fewer candidates than requested; missing slots were not filled with ineligible series.
- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
