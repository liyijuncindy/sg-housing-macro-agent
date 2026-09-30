# Validation record

Checked on **1 October 2026, Singapore time**, using Python 3.12.14. This document distinguishes observed results from planned or unverified behaviour.

## Automated tests

```bash
python -m unittest discover -v
```

**Observed: 82 tests passed.** Full output is saved in [evidence/tests.txt](evidence/tests.txt).

- 41 engine tests: true-calendar baselines, missing quarters, zero denominators, percentage/basis-point units, date cutoffs, population reference dates, quality windows, staleness and family selection.
- 17 agent tests: mocked Responses calls, exact evidence IDs, input/output continuity, bounded correction, prohibited numeric prose, reasonable qualitative phrasing, missing credentials and redaction. These are protocol tests, not live model calls.
- 15 source tests: captured official GDP/population/SORA responses, exact series requests, source identity/metadata consistency, cell-limit rejection, API errors and retry audit trails.
- 9 pipeline tests: full workflow with explicit synthetic fixtures, partial and total failure, cutoff-filtered CSV, table rendering, immutable output, environment handling, replay and tampering.

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

## Live model status

**Not yet verified against a real OpenAI API account.** The optional SDK is installed in the development environment and the adapter passes mocked protocol tests, but the local API key was not configured at this checkpoint. The delivered sample deliberately uses `rules` mode and makes no claim of a live Agent run.

After local configuration, run the `--mode llm` command in the README. The application records actual tool calls, output validation and token usage. A success can then be documented separately; a failure must be investigated rather than replaced with a mock transcript.

## Remaining limitations

No held-out forecasting evaluation, historical-vintage reconstruction, automated revision comparison or semantic proof of generated market statements has been performed. Update cadence is inferred from official observation frequency where a release calendar is unavailable. These limits are stated in the report and engineering notes.
