# Singapore housing: macroeconomic research brief

**Reporting date:** 2026-10-01  
**Run:** `siliconflow_glm_verified_run`  
**Generated at:** 2026-10-01T12:13:55+00:00  
**Analysis mode:** Live SiliconFlow Chat Completions tool-calling agent (zai-org/GLM-5.3)  
**Data basis:** Latest downloaded vintage filtered by observation reference date (or period end); not a historical point-in-time information set.

> This is a study of possible indicators, not a price forecast or evidence of causation. The reporting date filters observation dates; the values are from the latest downloaded vintage. Observation-level release dates and historical revisions are generally unavailable. This report does not recreate the information set known on the reporting date.

## Candidate selection

Evaluated 16 candidates and selected 5. siliconflow_chat_completions_constrained_agent

Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality and the reporting date. Predictive validation against housing outcomes is not performed in this first version.

**Source strategy:** SingStat first for every candidate; bounded request retries, independent candidates continue, transient failures rechecked; reviewed per-candidate backups enabled. Per-candidate attempts and actual routes are recorded in [source_routes.json](source_routes.json).

[完整指标池表：定义、纳入理由、官方来源和本次选择](indicator_pool.md) · [可搜索的表格预览](indicator_pool.html)

| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |
|---|---|---|---:|---|---|
| Resident Population (M810001:2) | population_demand | 2026 | 100 | Excluded | Eligible and complete. Resident population growth is conceptually sound for sale price and rent support, but its dwelling-demand content is largely conveyed through household counts, which were retained in preference within the same population/demand family; the series remains useful and is not fully substituted. |
| Non-Resident Population (M810001:5) | population_demand | 2026 | 100 | Excluded | Eligible and complete, with the clearest mechanism to private rental demand among the population counts. Not retained because the same population/demand family was already represented by resident households and the count also includes residents in dormitory-style arrangements that do not translate into ordinary rental demand; this is a deliberate family-coverage and capacity judgement, not a failure of relevance. |
| GDP In Chained (2015) Dollars (M015661:1) | economic_activity | 2026-Q2 | 95 | Excluded | Eligible and complete, with relevant activity and confidence effects on both purchases and rents. Not retained because the selection already mixes monthly, quarterly and annual frequencies, leaving no room within the limit for a broader activity proxy; this reflects capacity and partial coverage rather than any data-quality failure. |
| Resident Unemployment Rate, (SA) (M182342:2) | labour_market | 2026-Q2 | 95 | Excluded | Eligible, complete and timely labour-market stress signal that may work in the opposite direction to demand. Not retained because the shortlisted channels already span financing, credit, supply and household demand, and the resident unemployment rate covers a narrower labour channel with no distinct family coverage gain; this is a capacity choice, not an irrelevance judgement. |
| Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents (M184101:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible and complete with a direct affordability channel, though its useful history begins relatively late in the window and a mean per employed person can be pulled about by high earners. Not retained because no household income or earnings measure was retained and the limit was exhausted on other priority channels; exclusion is a capacity judgement and the series would be a complementary, not redundant, addition. |
| Personal Disposable Income (Nominal) (M016081:1) | household_income | 2026-Q2 | 95 | Excluded | Eligible, complete and timely. A valuable aggregate purchasing-power complemant that could substitute for a household-level income measure only with care, since it is aggregate, nominal and not per household. Not retained as the selection already includes the household-side and credit-side of capacity, and the limit was filled by multi-channel coverage; this exclusion does not imply substitution. |
| Compounded Singapore Overnight Rate Average (SORA) - 3 Month (M700071:23) | financing_cost | 2026-08 | 97.14 | Selected | Retained. Eligible, most complete and timely monthly series in the pool, and the only financing-cost measure: it is the benchmark to which floating-rate housing finance references, giving a direct borrowing-cost channel for sale prices and a tenure and landlord-carry channel for rents. |
| Consumer Loans - Housing And Bridging Loans (M701091:1.2.1) | housing_credit | 2026-08 | 97.14 | Selected | Retained. Eligible, complete, high-quality monthly housing-specific credit stock from the banking system. It complements the benchmark rate by capturing the quantity side of housing finance that financed purchase demand depends on, and it is the only representative chosen from the housing credit family. |
| All Types Private Residential Properties Available (M400841:1) | completed_supply | 2026-Q2 | 95 | Selected | Retained. Eligible, complete quarterly completed private residential stock from URA. It measures the current supply base that prices and rents must be absorbed against, and it is also the documented denominator against which the vacant-unit count must be read, making it a deliberately retained complement within the supply family. |
| All Types Private Residential Properties Vacant (M400841:2) | vacant_supply | 2026-Q2 | 95 | Selected | Retained. Eligible, complete quarterly count of vacant completed private units, a direct measure of market slack that is the closest supply-side lever on rents and, more weakly, on prices. It shares the supply family with the stock count, but they answer different questions (total base versus idle units) and the count must be interpreted against the stock, so retaining both is justified. |
| Total Non-Landed Properties (M400391:2) | future_supply | 2026-Q2 | 95 | Excluded | Eligible and complete. The non-landed pipeline was excluded only on capacity and family-coverage grounds, and not because its completions arrive later: prospective supply can affect prices today through an expectations channel, well before completion, and would enhance forward-looking supply coverage, but the family was already represented by the completed-stock and vacant-unit measures. It remains a useful, complementary signal that is not fully substituted. |
| All Items (M213751:1) | inflation | 2026-08 | 97.14 | Excluded | Eligible, complete and timely with a small relative base period. Excluded for scope rather than availability: it is a very broad basket whose housing-related components overlap with rents, so it is not an independent causal housing driver and risks circularity, and the inflation family did not earn a slot within the limit. |
| Resident Households (M810371:1) | population_demand | 2025 | 100 | Selected | Retained. Eligible and complete with no missing observations. Household counts are the closest demand-side analogue to occupied dwelling space, potentially better suited to purchase and rental demand than population counts, and it is the only representative retained from the population/demand family. Annual frequency is an accepted limitation rather than a block. |
| Median Monthly Household Employment Income Including Employer CPF Contributions (M810361:5) | household_income | 2025 | 100 | Excluded | Eligible and complete with the clearest household-level affordability content among the income measures, distinct from aggregate income or income per employed person. Not retained because no income series was retained and the limit was filled by higher-frequency financing, credit and supply measures; annual cadence limited marginal model value despite excellent quality and a coherent mechanism, and exclusion does not substitute this signal for any retained series. |
| Employment (Persons) As At Year End (M183111:7) | employment_level | 2025 | 100 | Excluded | Eligible and complete. Annual total employment captures aggregate earned income and work-related housing demand, but it counts migrant domestic workers whose accommodation does not necessarily translate into separate rental demand and it does not reflect earnings. Not retained for capacity, since resident household demand and financing channels were prioritised, and because quarterly labour-market signals were viewed as complementary rather than interchangeable. |
| Total HDB Flats (M400751:1.1) | public_housing_supply | 2026 | 100 | Excluded | Eligible and complete. The public-housing stock offers genuine tenure-substitution context for both sales and rents, but as an annual aggregate stock it is not new supply or availability, and its annual cadence and indirect linkage were outweighed by private-market supply measures already retained within the same supply family. This is a capacity and channel-specificity judgement, not a quality failure. |

## Compounded Singapore Overnight Rate Average (SORA) - 3 Month

- **Series:** `M700071:23`; **Theme:** financing_cost
- **Source:** MONETARY AUTHORITY OF SINGAPORE via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M700071)
- **Definition:** Three-month compounded Singapore Overnight Rate Average (SORA), observed at month-end and expressed as an annual percentage rate.
- **Coverage:** Singapore-dollar benchmark interest rate; not an individual mortgage offer.
- **Unit:** Per Cent Per Annum; **Observation frequency:** M; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Monthly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 1.1863 Per Cent Per Annum in 2026-08 (evidence `M700071:23:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 14/09/2026; **Retrieved:** 2026-10-01T12:15:28+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 5.09 | basis points | M700071:23:previous_period |
| year_on_year | 2026-08 | 2025-08 | -37.75 | basis points | M700071:23:year_on_year |

**Possible sales-market channel:** This is the Singapore-dollar benchmark rate to which floating-rate housing finance references. A higher reading may feed into mortgage repricing at rollover or reset, raising the user cost of ownership and tightening effective borrowing capacity, which may in turn weigh on purchase demand and transaction volumes. Falling readings may ease mortgage serviceability and support debt-financed purchase demand, subject to spreads, fixed-rate lock-in periods and refinancing terms.

**Possible rental-market channel:** Ownership financing costs may shift the relative attractiveness of owning versus renting, potentially diverting some households into the rental market, while landlords facing higher carry costs may seek rent adjustments, leaving the net direction ambiguous a priori. The yield-based discount framing also links the benchmark to how rental streams are valued. This interpretive ambiguity does not make it less useful; both directions are plausible and the series still captures an economy-wide pricing lever.

**Possible lag:** The underlying series is a month-end snapshot that reports with a short delay. Pass-through depends on mortgage pricing, reset dates and fixed-rate periods, so effects may operate rather quickly for some borrowers but spread over subsequent months or quarters as repricing occurs.

**Limitations:** A month-end observation rather than a monthly average; not an individual mortgage offer or a lending-spread measure. Mortgage spreads, fixed-rate loans, refinancing terms and policy settings constrain transmission, so rate movements by themselves cannot determine prices or rents. Observations are the latest captured vintage and may have been revised; retained facts are the latest available, not automatically the current period.

Referenced evidence: `M700071:23:latest`, `M700071:23:previous_period`, `M700071:23:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M700071_5ec2ab86786f7bd2.json`; SHA-256 `844467d877f0fc311402be16f7fb1e606b894eb34185683c8a20f9039d4c70a2`.

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
- **Source table last updated:** 30/09/2026; **Retrieved:** 2026-10-01T12:15:28+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-08 | 2026-07 | 0.7422 | % | M701091:1.2.1:previous_period |
| year_on_year | 2026-08 | 2025-08 | 7.2804 | % | M701091:1.2.1:year_on_year |

**Possible sales-market channel:** This is the outstanding stock, not a flow of new lending, of commercial-bank consumer housing and bridging loans to residents. Expanding housing credit may accompany financed purchase demand, easing budget constraints for buyers and supporting transactions and prices. The direction may also run the other way, with rising prices drawing out more borrowing, so the series is plausibly co-determined with the housing market rather than purely an exogenous driver.

**Possible rental-market channel:** Credit conditions may influence the choice between owning and renting, since access to housing loans shapes whether households can exit the rental market in the first place. As a demand-side context it may capture whether loan-reliant tenures are expanding, feeding into rental demand pressure.

**Possible lag:** The underlying series is reported monthly at month-end with a short delay. Stocks adjust gradually as new loans, refinancing and repayments accumulate, so movements may lag transactions and reflect lending conditions formed in earlier periods.

**Limitations:** It does not capture lending outside commercial banks or lending to non-residents, is not origination flow or credit availability, and repayments net against new lending. Revised reporting for the covered consumer loans series begins partway through the retained span, so levels should mostly be read thereafter; observations may also be revised, and retained values are the latest available snapshot rather than guaranteed current releases.

Referenced evidence: `M701091:1.2.1:latest`, `M701091:1.2.1:previous_period`, `M701091:1.2.1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M701091_11d6417c6fe41133.json`; SHA-256 `b8bc0b0d9f1fa8d7fe20072630210799fc9d32057a3ea71765b2032259933e8d`.

Exact source row: `1.2.1` in table `M701091`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M701091:1.2.1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 256,563.5 and 254,673.3.
- `M701091:1.2.1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 256,563.5 and 239,152.3.

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
- **Source table last updated:** 24/07/2026; **Retrieved:** 2026-10-01T12:15:29+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 0.0981 | % | M400841:1:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | 1.0565 | % | M400841:1:year_on_year |

**Possible sales-market channel:** This series is the completed private residential stock: all landed and non-landed units with issued occupation permits, excluding public housing, hostels and comparable dwelling types. Stock growth may gradually ease supply constraints relative to demand, which could temper upward pressure on prices, subject to location and unit-type balance. Because it is a slow-moving stock, its information is largely about base and trend rather than short-term timing.

**Possible rental-market channel:** A larger completed stock raises the effective ceiling on rental supply, since additional homes may be released to the rental market, potentially widening alternatives for tenants, though the degree depends on how many completions are actually let out and how quickly they are absorbed. The series also gives the number of habitable homes from which market slack can be judged.

**Possible lag:** The underlying series is quarterly with a quarterly reporting delay. Because stock accumulates slowly, its effect may unfold over subsequent quarters, and the timing of absorption may lag completion. As a denominator and trend measure, its signal works over longer horizons.

**Limitations:** It counts habitable physical homes, not homes actively marketed for sale or rent, and stock alone says nothing about idleness: the vacant count, which should be divided by this stock for matching periods to judge market tightness, carries the clearest signals. Interpretation as a flow driver would be a mistake, since it is a slow-moving base rather than newly supplied homes.

Referenced evidence: `M400841:1:latest`, `M400841:1:previous_period`, `M400841:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M400841_9cbe20a8bfdb6540.json`; SHA-256 `e6363fdf9c307229226c70f6210a01bed31099f9e2cca622a1f7faa1a8741cbd`.

Exact source row: `1` in table `M400841`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M400841:1:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 424,581 and 424,165.
- `M400841:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 424,581 and 420,142.

</details>

## All Types Private Residential Properties Vacant

- **Series:** `M400841:2`; **Theme:** vacant_supply
- **Source:** URBAN REDEVELOPMENT AUTHORITY via [SingStat Table Builder](https://tablebuilder.singstat.gov.sg/table/TS/M400841)
- **Definition:** Number of vacant completed private residential units at quarter-end, not the vacancy rate.
- **Coverage:** All landed and non-landed private residential units; same exclusions and coverage as the completed stock in table M400841 row 1.
- **Unit:** Number Of Units; **Observation frequency:** Q; **Seasonal adjustment:** Not labelled as seasonally adjusted
- **Update frequency:** Quarterly observation frequency in official metadata; expected update cadence is inferred, not guaranteed. Release calendar and individual observation publication dates are not confirmed.
- **Latest usable observation:** 26,961 Number Of Units in 2026-Q2 (evidence `M400841:2:latest`)
- **Observation reference date:** Period end used conservatively
- **Source table last updated:** 24/07/2026; **Retrieved:** 2026-10-01T12:15:29+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| previous_period | 2026-Q2 | 2026-Q1 | 3.0698 | % | M400841:2:previous_period |
| year_on_year | 2026-Q2 | 2025-Q2 | -10.2108 | % | M400841:2:year_on_year |

**Possible sales-market channel:** This series counts vacant completed private residential homes, not a vacancy rate: it measures unutilised homes inside the habitable stock. A rising count may point to softer absorption and weaker effective demand relative to occupancy opportunities, potentially easing upward pressure on prices, though location and specific demand shifts matter. A falling count may point to strengthening take-up and tighter effective utilisation, potentially supporting pricing power.

**Possible rental-market channel:** Vacancy is arguably the most direct supply-side lever on rents in this pool: vacant homes are the portion of the stock available to let, and a rising count signals widening options and landlord competition, potentially softening rent pressure, while a falling count may point to tightening availability and pricing power for landlords, assuming no contraction of the stock itself.

**Possible lag:** The underlying series is quarterly with a quarterly reporting delay. Vacancy reflects conditions after the fact, so price and rent responses may follow over subsequent quarters rather than appear immediately. Its own cycle may also lag the lease and sale decisions that determine it.

**Limitations:** It is a count and idleness measure that must be divided by the completed private residential stock for matching periods to obtain a vacancy rate; a rising raw count can coexist with a falling rate when the stock is growing rapidly. It says nothing about asking rents, unit types, location mix or how occupants are housed in practice; retained observations are the latest available vintage, which could have been revised.

Referenced evidence: `M400841:2:latest`, `M400841:2:previous_period`, `M400841:2:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M400841_de38dc09e41862f3.json`; SHA-256 `0104a610532cf4ac51fba4e4ee1eceed2f7960241c4bbf9e818ed72ec5ac8d54`.

Exact source row: `2` in table `M400841`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M400841:2:previous_period`: `(latest_value / base_value - 1) * 100`; inputs 26,961 and 26,158.
- `M400841:2:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 26,961 and 30,027.

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
- **Source table last updated:** 30/06/2026; **Retrieved:** 2026-10-01T12:15:30+00:00

| Comparison | Latest period | Base period | Change | Unit | Evidence |
|---|---|---|---:|---|---|
| year_on_year | 2025 | 2024 | 1.6195 | % | M810371:1:year_on_year |

**Possible sales-market channel:** This is an annual count of resident households, not the number of newly formed households and not population. Because it measures the number of resident groups in the economy that could occupy a dwelling, it may better represent potential purchase demand than population alone, subject to affordability, tenure choices and existing ownership, and growth in the household base may support underlying purchase demand over time.

**Possible rental-market channel:** More resident households may support rental demand where those households rent rather than buy, so the count contributes to the tenant side of the market alongside population, conditional on how households choose between owning and renting. It cannot, by itself, indicate how many households rent or how intensively space is used.

**Possible lag:** The underlying series is annual with no claimed timing link, and, in the retained vintage, annual observations through the most recent available period. Household-driven demand context is structural, so it may be interpolated and any effects may build over multiple quarters rather than within one; use in a quarterly prediction setup should smooth the annual cadence appropriately.

**Limitations:** The measure is a level of households, not gross formations, and differences over time are net changes that also ignore dissolutions, splits and recombinations. It comes from statistical releases combining the census, household surveys and administrative sources, with possible discontinuities, sampling variability and revisions; it does not capture affordability, foreign tenants or tenure mixes, and retained observations are the latest available snapshot of a series that may be restated.

Referenced evidence: `M810371:1:latest`, `M810371:1:year_on_year`.
- Data warning: Latest-vintage snapshot: period/reference-date filtering does not establish what was historically available or exclude later revisions. Known publication dates are respected; unknown publication dates are not inferred.
- Data warning: Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.

<details><summary>Trace the numbers</summary>

Raw response: `raw/tabledata_M810371_8461ccdf2c645031.json`; SHA-256 `3b1c98d7f8191a8c4ab000444fe34c827a556ab416c85e2623154d79c458595d`.

Exact source row: `1` in table `M810371`. The observations in `evaluations.json` retain original period, value and raw column index. Each calculated change retains the formula and both input observations.

- `M810371:1:year_on_year`: `(latest_value / base_value - 1) * 100`; inputs 1,487,100 and 1,463,400.

</details>

## Run limitations and reproducibility

- Mixed observation frequencies are preserved; annual data are not interpolated to months.
- Private residential series retain their own coverage and are not automatically generalised to HDB housing.
- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.
- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.
- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.
