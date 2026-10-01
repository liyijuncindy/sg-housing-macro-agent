# Validation record

Checked on **1 October 2026, Singapore time**, using Python 3.12.14. This document distinguishes observed results from planned or unverified behaviour.

## Automated tests

```bash
python -m unittest discover -v
```

**Observed: 205 tests passed.** The suite was rerun for the SingStat-priority revision; complete output is saved in [evidence/tests.txt](evidence/tests.txt).

- 41 engine tests: true-calendar baselines, missing quarters, zero denominators, percentage/basis-point units, date cutoffs, population reference dates, quality windows, staleness and family selection.
- 33 agent tests: mocked Responses and SoCLaaS Chat Completions calls, provider and credential isolation, truncated replies, compact fact payloads and precise repair feedback, exact evidence IDs, input/output continuity, bounded correction, prohibited numeric prose, reasonable qualitative phrasing, missing credentials and redaction. These are protocol tests, not live model calls.
- 31 source tests cover current-notice recognition, historical/future/JSON-text non-matches, retry and recovery, incomplete response streams, independent subsequent requests, bounded diagnostic capture, official-response parsing, identity checks and truncation rejection.
- 33 pipeline tests cover independent candidate continuation after failed discovery, two-pass transient failure handling, catalogue-dependent selection limits, saved-snapshot verification including failed-response hashes, full synthetic workflows, all-source failure before model invocation, immutable output and replay.
- 12 MOM tests: quarterly resident/SA selection, CSV precision, workbook title/unit/coverage validation, preliminary markers, source locators, formula rejection and catalogue-definition drift.
- 19 MAS tests: public form selection, repeated annual headers, value-date versus publication-date grouping, complete month boundaries, weekend endpoints, null terminal values, malformed rows and source identity.
- 16 independent transport/integration tests: original-file auditing, public-host restrictions, bounded retries, HTTP 206 rejection, SingStat-first routing, delayed rechecks, per-candidate backup selection, strict SingStat policy, failed fallback isolation, mixed-source saved snapshots and replay.
- 16 indicator-pool tests: complete catalogue joins, actual-versus-configured sources and definitions, missing-data status, absence of fabricated values/zero scores, exact decision attribution, reviewed-note hashes, safe HTML/Markdown output, and saved-source/export disclosures.
- 4 indicator-pool integration tests: immutable offline export, tampered or uninventoried input rejection, automatic table output in new runs, and byte-identical replay of all three earlier sample reports.

## Historical unified indicator-pool table

```bash
python -m housing_agent indicator-pool examples/independent_sources_run --output examples/indicator_pool
```

The [exported table](../examples/indicator_pool/indicator_pool.md) presents all twelve candidates from the saved independent-source run. The three downloaded MOM/MAS indicators retain their observed values, quality scores and original decisions. The other nine were skipped by the old stop-after-maintenance policy; this is not evidence that all nine were individually requested and failed. The historical export is retained unchanged, with no substituted old observations or displayed placeholder zero scores. Reviewed Chinese economic rationales remain separate from saved selection reasons. Actual source metadata takes precedence over configured routes, including when exporting the earlier SingStat runs.

This is an offline presentation export, not another data refresh or model trial. Its manifest records the original run's manifest hash, each presentation input hash and the three generated file hashes. The original sample directories remain unchanged. Future completed workflows produce the same Markdown, searchable HTML and JSON artifacts automatically and include them in the run inventory.

The HTML table was inspected in a local browser. Searching `SORA` displayed one candidate; searching `维护` displayed the nine unavailable candidates; clearing the search restored all twelve. The table retains all seven columns with horizontal scrolling on narrow windows and expandable original evidence. Final export hashes and row equality against the current table builder were verified.

## Live independent-source workflow

```bash
python -m housing_agent run --as-of 2026-10-01 --mode rules --output examples/independent_sources_run
```

**Observed: completed with explicit partial-coverage warnings from a clean tracked checkout at `14b80b7`.** The run made five HTTP attempts: one SingStat discovery request returned the maintenance notice, both MOM files downloaded successfully, and MAS form GET plus CSV POST succeeded. The other nine candidates were excluded without further SingStat requests. Three candidates passed the same quality gates and were selected; no old source snapshot was substituted. This was a rules-mode source integration check with **zero model calls and zero model tokens**, not another live SoCLaaS trial. End-to-end time recorded by the workflow was 0.963 seconds for this particular run, not a performance guarantee.

| Selected source | Latest observation | Captured history |
|---|---|---|
| MOM seasonally adjusted resident unemployment | 2026 Q2: 2.9% | 138 quarters |
| MOM mean employment income, including employer/platform CPF, excluding bonuses | 2026 Q2: SGD 6,605, preliminary | 21 quarters |
| MAS compounded three-month SORA, sampled at month-end | September 2026: 1.2336% per annum | 255 sampled months, 252 non-null |

The initial integration run exposed MAS's repeated annual CSV headers. That attempt correctly excluded the unparsed MAS series and reported only two available candidates. The parser was corrected to accept identical repeated headers while resetting date context, and regression tests were added before the final fresh run. No failed run was relabelled as successful.

An independent raw-file audit checked **414 normalized observations** against original CSV rows or XLSX cells and recalculated **five changes** using decimal arithmetic. Cross-source comparison against the original SingStat snapshot found **410 matching non-null observations and zero differences**: 138 unemployment quarters, 21 income quarters and 251 SORA months. Grouping MAS by publication date instead of value date would have produced 247 mismatches. See [the validation evidence](evidence/independent-source-validation.json) and [the resulting report](../examples/independent_sources_run/report.md).

Replay verified all **17 run files** with no network/model calls and produced identical report bytes (SHA-256 `5dd1d793e43e401a3ae4fb6bd399b75822140f247fa91643e3ede6841e262709`). The original SingStat and SoCLaaS reports also still replay identically. A new non-editable wheel was installed into the clean environment without the optional OpenAI SDK; all three raw parsers reproduced the saved observations and replay succeeded from outside the repository. `pip check` passed. See [the installed-package check](evidence/independent-source-install-check.json).

## Live official-data workflow

```bash
python -m housing_agent run --as-of 2026-09-30 --mode rules --output examples/sample_run
```

**Observed: completed successfully.** This sample was generated from actual public SingStat responses, not synthetic observations. It contains twelve evaluated candidates, thirty successful requests (official catalogue searches, table metadata and exact series), and five selected indicators. The manifest identifies the code commit and confirms the tracked worktree was clean at the start of the run.

The selected baseline set is resident population, CPI, compounded SORA, housing credit and real GDP. This is the deterministic quality/diversity baseline's result, not a claim that these are the economically optimal predictors. Every candidate's inclusion or exclusion appears in the report.

An independent audit followed every normalized value back to its raw table, row and column index: **2,189 original observations checked**. It also recalculated **19 available changes** with decimal arithmetic. All checks passed; see [evidence/raw-audit.json](evidence/raw-audit.json).

## Replay and fresh installation

A new isolated environment installed the project as a non-editable wheel. The packaged catalogue contained all twelve candidates. The optional OpenAI SDK was absent from that environment, demonstrating that core data/replay functionality does not depend on it.

From outside the source checkout:

```bash
python -m housing_agent replay /path/to/project/examples/sample_run --output /new/path/replayed.md
```

**Observed: forty run files verified, zero network calls, zero model calls, byte-identical report.** Report SHA-256:

```text
d76430d7eb42579694fd1bb2523683d5ed239e271148daf85d6952523c9d39d6
```

The editable installation's `housing-agent --help` entry point worked and `pip check` reported no broken requirements. Tested optional dependency versions are in `requirements-llm.lock`.

## Data-dependent selection demonstration

The same captured observations were evaluated at three different observation cutoffs. This is a **retrospective sensitivity check using today's vintage**, not historical availability or a forecasting backtest. Results and exclusion reasons are saved in [evidence/selection-sensitivity.json](evidence/selection-sensitivity.json).

At the 2020 cutoff, employment-income and housing-credit candidates lack usable observations and fail the gates. The selected set is GDP, disposable income, unemployment, CPI and housing pipeline. At the 2026 cutoff the selected set differs, as reported above. This demonstrates that the program has not hard-coded the original five indicators as the answer. Further target-based evaluation is still needed to establish predictive usefulness.

## Concrete edge cases and improvements

1. **Wrong year-on-year baseline when a quarter is missing.** A regression demonstrates that row-position selection can produce 44.444...% while the correct calendar comparison is 30%. The implementation indexes the actual same quarter in the previous year and retains the input evidence; absent baselines return unavailable values.
2. **Unfiltered API truncation.** The captured CPI response contains exactly 5,000 observation cells and ends partway through a series. See [the original response](evidence/cpi-unfiltered-response.json) and [finding](evidence/truncation-finding.json). The client now requests exact rows and rejects a response that reaches the per-series cap.
3. **Real date formats and reference dates.** Captured quarterly responses use `YYYY nQ`. Population has an end-June reference date. Fixture tests ensure quarterly observations are not discarded and current-year population is not excluded until December.
4. **Processing cutoff and report table layout.** Review identified a CSV that retained post-cutoff observations and an unavailable-comparison warning that split a Markdown table. Both were fixed and regression-tested. Full history remains in `normalized.json`; `processed.csv` follows the report cutoff.

## Live model integration

NUS SoCLaaS is the selected provider for this integration. The service's authenticated model listing on 1 October 2026 reported `default` as an alias of `qwen3.6:35b`; the integration pins the explicit ID. See [the captured model metadata](evidence/soclaas-models.json).

A fresh official-data run encountered persistent HTTP 502 responses across twenty logical source requests and sixty bounded HTTP attempts. It failed before any LLM call and did not produce a report. [The failure audit](evidence/soclaas-source-outage.json) is preserved. Subsequent integration tests explicitly reuse the earlier verified official snapshot; they are real model calls but not a successful fresh source refresh.

The first live adapter probe completed in 64.938 seconds and six requests, using 149,733 input tokens and 6,554 output tokens (156,287 total). Three submissions repeated a forbidden numeric tenor label before the model corrected it. Its full original [trace](evidence/soclaas-first-probe/agent_trace.json), [selection](evidence/soclaas-first-probe/selection.json) and [semantic review](evidence/soclaas-first-probe/review.json) are preserved. Semantic review also found mistaken family equivalence, an aggregate-versus-household income distinction, and overly strong exclusion reasons. A syntactically valid submission is therefore not sufficient evidence of a sound economic interpretation.

The follow-up implementation removes duplicate fact payloads, sends shared quality policy text once per result, identifies the offending numeric token in repair feedback, and clarifies exact families, aggregation, scope and cautious exclusion reasoning. Full raw data and evaluated facts remain available in the saved run.

The next full saved-source workflow still exhausted its eight-call budget on numeric population-definition years, despite a smaller payload. It used 141,527 input and 7,021 output tokens (148,548 total) in 66.409 seconds. No report was produced. The complete failed run is preserved in [evidence/soclaas-repair-failure](evidence/soclaas-repair-failure/manifest.json). This failure demonstrates a real instruction-following limitation of the tested model/prompt combination, not a network error. A targeted follow-up gives full numeric fragments and explicit semantic rewriting feedback without relaxing the numeric/evidence checks.

The final saved-source CLI run completed with the explicit snapshot warning. It generated [a real SoCLaaS report](../examples/soclaas_verified_run/report.md) from a clean tracked checkout at `e639a4a`. It took **21.666 seconds end-to-end** (21.603 seconds in the model adapter), using **45,423 input + 2,233 output = 47,656 tokens across four requests**. A numeric reference-year submission was rejected, and the next forced correction passed. All selected IDs and evidence belong to the inspected candidates. The final five are aggregate personal disposable income, non-landed housing pipeline, SORA, non-resident population and completed private residential stock.

The trace contains model text as returned, not manually polished text. Missing individual model exclusion reasons are explicitly labelled as system exclusions in the saved report. Protocol acceptance is distinct from economic and editorial quality; the [semantic review](evidence/soclaas-final-review.json) records no major issue in the selected narratives, but flags seven system-supplied exclusions and the unclear word “Aggregatemean” in a short income selection reason. The source definition and main narrative correctly identify aggregate total income, not a mean. Four narratives repeat all supplied mechanism fields verbatim; the fifth changes only its limitation. This run demonstrates real constrained selection and evidence organization, not independent discovery of economic mechanisms.

Replay verified **41 files**, made zero source/model calls and generated a byte-identical final report with SHA-256 `5162ae5ddd22c1dc08dd79a9f2eaf8264f7c7f18b24733f5da8d10fbc9f5ae57`. Across all three development model trials, actual reported consumption was **352,491 tokens** and eighteen requests. [The machine-readable trial summary](evidence/soclaas-trials-summary.json) separates each attempt. These changing development trials do not measure a production success rate, predict housing prices, or prove unattended reliability. The final run's token use is about seventy percent lower than the first probe, but this is an observed pair of runs with different prompts and selections, not a controlled benchmark.

The OpenAI Responses path remains supported by offline protocol tests; it has not been verified with a real OpenAI account in this task.

## Remaining limitations

No held-out forecasting evaluation, historical-vintage reconstruction, automated revision comparison or semantic proof of generated market statements has been performed. Update cadence is inferred from official observation frequency where a release calendar is unavailable. These limits are stated in the report and engineering notes.

## Historical maintenance responses and corrected source routing

A follow-up at 16:50 SGT on 1 October 2026 received an explicit maintenance page from both the Table Builder API and homepage; the main SingStat website returned HTTP 200. Agent and browser User-Agent strings produced the same maintenance response. [The recorded diagnosis](evidence/singstat-maintenance-diagnosis.json) establishes the response body at those request times; it does not establish a persistent site-wide outage or its underlying technical cause. The later 17:19 SGT discovery request also returned a maintenance page. At 19:16 SGT, a fresh check received normal HTTP 200 JSON from the population metadata and discovery endpoints, and a subsequent rules run downloaded all twelve original candidates. See [the recovery response evidence](evidence/singstat-recovery-check/diagnosis.json).

The earlier single-source implementation identified that explicit notice and stopped immediately, with a maintenance category and recovery advice. Its live check made **one HTTP request**, made **zero model calls** and created no report; see [the historical check](evidence/maintenance-stop-check.json). This behavior is superseded in both policies. Each request now has bounded retries; independent candidates continue; retryable candidate failures receive a later second pass. Only then can the default policy use a reviewed MOM/MAS backup for that individual candidate. The `singstat` policy uses the same retries and continuation without backups. Historical announcements or maintenance text within normal JSON/page content do not activate the current-maintenance classification.

The accessible main-site national-accounts page was also fetched directly and its displayed GDP rows extracted successfully; see [the independent source feasibility probe](evidence/direct-official-gdp-probe.json). These latest/previous observations are not a replacement for a complete historical dataset and that GDP route is not integrated.

Independent MOM unemployment CSV and quarterly income XLSX downloads, and the MAS public daily compounded-SORA CSV export, remain integrated as reviewed fallbacks. Their earlier live validation and [recorded routes](evidence/independent-official-source-routes.json) are distinct from the separate GDP feasibility check.
