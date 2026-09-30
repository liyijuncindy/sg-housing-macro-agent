# Engineering report: Singapore housing macroeconomic data agent

## Objective and scope

This first version implements a date-driven CLI workflow for publicly accessible macroeconomic, demographic, financial and housing-supply indicators. It downloads actual official observations, records provenance, computes appropriate changes and generates an analytical report in the same run. It does not train a housing-price model or claim that the selected predictors have established out-of-sample predictive power.

The user explicitly challenged selecting a fixed group of indicators before seeing data. The implementation therefore evaluates a bounded catalogue of twelve candidates and records selection decisions for all of them. The selected set can change with the reporting date, source availability, data quality, requested capacity and agent judgement. The bounded catalogue itself is a reviewed input, not a claim of exhaustive autonomous discovery.

## Data selection

The candidates cover resident and non-resident population, real GDP, resident unemployment, employment income, disposable income, compounded SORA, housing credit, completed stock, vacant units, housing pipeline and CPI. Several candidates are alternatives or complementary measurements within the same economic family. All are retrieved through SingStat, with original publishing institutions preserved. Using one public API reduces adapter complexity; this also concentrates operational dependence on one distributor.

Official keyword searches are captured before the reviewed candidate series are downloaded. The live search documents relevant available tables but cannot silently admit an unknown series into the supported catalogue. Exact row identifiers, names, units, frequency and definitions are validated before use. A new predictor must first be reviewed and added to the catalogue.

Eligibility uses finite, unique, parseable observations; frequency-specific minimum history; recent-window completeness; and recency. Scores combine history, completeness, recency and the ability to calculate comparisons. The ten-year scoring window prevents sparse early history from penalising a complete recent series. The full downloaded history remains available for audit. Thresholds and weights are design choices disclosed in the results, not statistically estimated evidence of predictor relevance.

The deterministic baseline chooses eligible candidates by quality while initially covering different economic families. Related housing stock, vacancy and pipeline measurements share a family. Ties use stable identifiers, so the baseline may exclude a relevant indicator simply because capacity is limited. The model mode can combine usability with reviewed economic mechanisms and coverage, subject to the same hard eligibility constraints. Neither selection method uses a housing outcome series to tune or claim predictive performance.

## Architecture and division of responsibility

Python's standard library provides HTTP retrieval, parsing, validation, calendar arithmetic, JSON/CSV storage, CLI routing and report rendering. No database server or web application is required. The optional OpenAI Python SDK supplies a direct Responses API tool loop rather than a large orchestration framework. This makes the allowed actions and saved evidence easy to inspect.

The LLM can list/search captured candidates, inspect their evaluated facts, and submit selected identifiers, decision reasons and qualitative interpretations. It cannot write executable code, supply arbitrary download URLs or bypass quality gates. Selected candidates must have been inspected. Evidence identifiers must belong to their selected series. Actual responses and tool calls are saved; bounded turns and per-request timeouts prevent an uncontrolled loop. API failures remain explicit, with no silent switch to a non-agent report.

Numbers are produced by ordinary code and inserted into a fixed report. Qualitative prose is checked for unsupported numeric content and evidence references; sales and rental mechanisms, possible lag and limitations are separate fields. These checks are deliberately limited: correct evidence identifiers do not prove a causal or economic statement. Human review is still required. Rules mode uses reviewed mechanism templates and is labelled accordingly.

## Time, transformations and provenance

Observation period, reference date, source-table update time and retrieval time are separate fields. Population uses its documented end-June reference date. Otherwise, period-end cutoffs are conservative. Known observation publication dates are honoured, but current SingStat responses generally lack observation-level release times and historical vintages. The first version therefore reports an observation-cutoff analysis using the latest captured vintage; it does not claim historical point-in-time availability. This limitation prevents treating these reports as leakage-free backtests.

Original frequency and units are retained. GDP and the selected non-seasonally-adjusted income series use year-on-year comparisons. Population, quantities and price indices use percentage changes; unemployment uses percentage points; SORA levels are annual percentage rates and changes are basis points. Missing calendar baselines and zero denominators return unavailable results with reasons. No forward-filling, interpolation or positional substitute is used.

Each change records its formula, both periods, both values and exact original observation positions. Each series references immutable raw files with SHA-256 hashes. Run records also preserve configuration, source requests, normalized data, decisions, generated text, code commit and source-file hashes. A new live request creates a new directory instead of overwriting a prior vintage.

Replay verifies all recorded file checksums and renders from the saved facts and narratives without network or model calls. It checks byte equality with the saved report. A changed renderer can legitimately fail exact replay; the recorded code version and hashes help restore the matching implementation. Replay does not resample a model or pretend to be a new autonomous analysis.

## Reliability and demonstrated improvements

Two concrete issues shaped implementation. First, an unfiltered official CPI response stopped at the API's default cell limit partway through a row. The client now requests exact series, rejects a series reaching the configured cell limit, and validates metadata identity. Second, official quarter labels use `YYYY nQ`; parsing is covered by captured-response fixtures as well as synthetic edge cases.

A nontrivial calculation test removes an intermediate quarter. A naive row-position comparison uses the wrong base and reports roughly forty-four percent growth; matching the actual calendar quarter yields thirty percent. The regression asserts the correct comparison and original evidence position. Other tests cover unavailable baselines, zero denominators, period/reference-date handling, stale and incomplete data, schema/unit changes, fabricated model evidence, model repair attempts, immutable runs, complete retrieval failure and tampered replay files. Precise commands, observed counts and live-run status are recorded in the validation document.

Retries are bounded and reserved for transient retrieval failures. Permanent HTTP/schema errors cause explicit candidate exclusion. A partial report lists failures and warnings; if no candidate qualifies, the run is marked failed and no report is fabricated. Current and original snapshots allow later review of revisions, but automated revision diffing and proactive schema monitoring are future work.

## Limitations and two additional weeks

The first priority would be verified release-calendar and historical-vintage support, with clearly defined real-time availability. Next, add housing price and rental indices as evaluation outcomes, specify lag hypotheses, split evaluation chronologically, assess stability across windows, and compare selection rules with held-out forecasting baselines. That would establish evidence of usefulness beyond data usability without confusing in-sample correlation with forecasting performance.

Other improvements include expanding reviewed candidate coverage, configurable quality policy, source-revision comparisons, richer schema-drift diagnostics, calibrated semantic review of generated explanations and a second official distribution route. Stronger coverage of HDB-specific dynamics would require appropriate definitions rather than generalising private-market data. Scheduled refreshes, notifications and a user interface are outside this first version.

## AI assistance disclosure

Codex assisted with source research, implementation, tests and documentation. Parallel assistants researched official interfaces, implemented calendar-aware validation and implemented the bounded model adapter. Outputs were integrated and checked against captured official responses, automated tests and complete CLI runs. Source facts and sample observations were not invented. Mock API tests validate protocol behaviour but are not represented as a successful live LLM call; validation status explicitly distinguishes them.
