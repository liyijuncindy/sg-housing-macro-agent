# Validation record

Checked on **1 October 2026, Singapore time**, using Python 3.12.14. This document distinguishes observed results from planned or unverified behaviour.

## Automated tests

```bash
python -m unittest discover -v
```

**Observed: 126 tests passed.** Full output is saved in [evidence/tests.txt](evidence/tests.txt).

- 41 engine tests: true-calendar baselines, missing quarters, zero denominators, percentage/basis-point units, date cutoffs, population reference dates, quality windows, staleness and family selection.
- 33 agent tests: mocked Responses and SoCLaaS Chat Completions calls, provider and credential isolation, truncated replies, compact fact payloads and precise repair feedback, exact evidence IDs, input/output continuity, bounded correction, prohibited numeric prose, reasonable qualitative phrasing, missing credentials and redaction. These are protocol tests, not live model calls.
- 21 source tests: explicit maintenance detection, immediate stop, plain-text diagnostic capture, retained generic-gateway retry, captured official GDP/population/SORA responses, exact series requests, source identity/metadata consistency, cell-limit rejection, API errors and retry audit trails.
- 31 pipeline tests: maintenance aborts before remaining source requests or model calls, provider routing and explicit saved-snapshot verification/reanalysis, full workflow with explicit synthetic fixtures, partial and total failure, cutoff-filtered CSV, table rendering, immutable output, environment handling, replay and tampering.

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

## Confirmed SingStat maintenance and source-route checks

A follow-up on 1 October 2026 received an explicit maintenance page from both the Table Builder API and homepage; the main SingStat website returned HTTP 200. Agent and browser User-Agent strings produced the same maintenance response. [The recorded diagnosis](evidence/singstat-maintenance-diagnosis.json) confirms this specific cause, rather than inferring it solely from HTTP 502.

The source client now identifies that explicit notice and the workflow stops immediately, with a maintenance category and recovery advice. A live check made **one HTTP request**, stopped in the recorded duration, made **zero model calls** and created no report; see [the check](evidence/maintenance-stop-check.json). Generic gateway errors without a maintenance notice still receive bounded retries. This improves client behaviour but does not restore the upstream service.

The accessible main-site national-accounts page was also fetched directly and its displayed GDP rows extracted successfully; see [the independent source feasibility probe](evidence/direct-official-gdp-probe.json). These latest/previous observations are not a replacement for a complete historical dataset. Independent official-file adapters remain a separate integration step.

Independent MOM unemployment CSV and quarterly income XLSX downloads, and the MAS public daily compounded-SORA CSV export, returned HTTP 200 during source-route checks. [Recorded routes](evidence/independent-official-source-routes.json) explain scope and frequency checks still needed before integration. These checks do not claim the main workflow already supports these alternate parsers.
