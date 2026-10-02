# Singapore Housing Macro Agent

Fetch official Singapore data, assess 16 explanatory candidates, select a small research dashboard, and generate an English housing-market report with traceable calculations.

The default CLI report is **version 2**: an executive summary, actual private price/rent and HDB resale outcomes, trend charts, vacancy with its matching denominator, exploratory correlations, retrospective walk-forward checks, and a complete English indicator pool. Numeric claims come from saved calculations. The model supplies qualitative selection judgements, which remain subject to review.

Quality scores measure data usability, not predictive importance. The checks do not establish causation, an optimal indicator set, historical publication-time forecasting ability, or a production price forecast.

**Submission report:** [complete English report](examples/english_submission_run/report.md), [HTML report](examples/english_submission_run/report.html), and [indicator pool](examples/english_submission_run/indicator_pool.md). This offline editorial presentation restores each selected indicator's update-cadence statement, sales and rental mechanisms, possible lag and limitations. Edited narrative fields are labelled separately from original model wording. It retains the October 1 observations, selected IDs and calculations, and makes no new source or model requests. See [submission checks](docs/submission-validation.md) and the [engineering report](docs/engineering-report.md).

The underlying live GLM run captured all 19 series from SingStat, made six model requests and finished in about 225 seconds. All 16 decisions have model reasons; original output is preserved in [the live run](examples/english_glm_v2_run/report.md). The [earlier reviewed presentation](examples/english_glm_v2_reviewed_run/report.md) remains immutable. See [original validation and cost](docs/report-v2-validation.md).

## Quick start

Python 3.11 or newer is required. Run from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[llm,charts]"
python -m unittest discover -v
python -m housing_agent run --as-of 2026-10-01 --mode rules --limit 5 --output runs/new-report
```

The output directory must be new. `--limit` is a maximum, not a requirement to fill unavailable slots. Rules mode uses deterministic quality/diversity selection and reviewed mechanism templates; it is labelled separately from a live agent run.

Offline replay needs no key, source connection, or optional dependencies:

```bash
python -m pip install -e .
python -m housing_agent replay examples/english_submission_run --output runs/replayed-report.md
```

Replay validates saved hashes and regenerates the exact Markdown report. Its destination must be a new file outside the original run. Historical examples remain immutable, including their original language and limitations.

New v2 runs record `report_fields_version=2`. Older snapshots without this marker use their original presentation when replayed, so adding report fields does not rewrite historical reports. Uncaptured candidates display **Not assessed**, rather than a placeholder quality score.

## Configure the live agent

Copy `.env.example` to `.env` only on first setup; edit an existing file in place. Keep keys local. `.env` is ignored by Git and must be excluded from archives.

```dotenv
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your_local_key
SILICONFLOW_MODEL=zai-org/GLM-5.3
```

```bash
python -m housing_agent run --as-of 2026-10-01 --mode llm --provider siliconflow --limit 5 --output runs/live-glm
```

SiliconFlow uses the fixed official `https://api.siliconflow.cn/v1` Chat Completions endpoint. Returned reasoning content is preserved in tool round trips. The agent discovers captured candidates, inspects every candidate, then submits a selection and an individual English reason for **every** candidate. Version 2 rejects missing decisions instead of adding system-authored reasons.

| Provider | Separate local settings | API style |
|---|---|---|
| SiliconFlow | `SILICONFLOW_API_KEY`, `SILICONFLOW_MODEL` | Chat Completions |
| NUS SoCLaaS | `SOCLAAS_API_KEY`, `SOCLAAS_MODEL` (tested: `qwen3.6:35b`) | Chat Completions |
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL` | Responses |

`--provider` overrides `LLM_PROVIDER`; `--model` overrides that provider's model setting. Providers never borrow one another's keys. Existing environment variables override local `.env`. Only allowlisted settings are loaded, without executing configuration text.

At most eight model requests are made, each requesting up to 4,000 output tokens. SiliconFlow also receives a requested 4,096-token reasoning budget, which is not a guaranteed hard cap. SDK retries are disabled. SiliconFlow timeout is 120 seconds per request; the other providers use 60 seconds. These limits are **not** a currency budget. Actual returned usage, cache/reasoning subsets, model IDs and timings are saved. API or validation failure remains a failed run; it never silently becomes a rules report.

## Official data and temporary failures

Every candidate is attempted independently through **SingStat first**. Version 2 adds three separate evaluation outcomes:

| Outcome | SingStat series | Published base |
|---|---|---|
| Private residential property price index | `M212261:1` | 2009 Q1 = 100 |
| Private residential rental index | `M212311:1` | 2009 Q1 = 100 |
| HDB resale price index | `M212161:1` | 2009 Q1 = 100 |

Outcomes are targets, not explanatory candidates. Private sales, private rentals and HDB resale retain different coverage. Rental coverage includes executive condominiums, whereas the completed private stock/vacancy series excludes them.

Temporary gateway errors, timeouts and current maintenance pages receive bounded retries. Other candidates continue, then transient failures receive a second pass. Only after this can the three reviewed MOM/MAS backups be used: resident unemployment, quarterly employment income and SORA. A single response never establishes a whole-site outage. Permanent errors and changed definitions fail explicitly. Routing and limited error-response prefixes are saved.

- `--source-policy auto`: SingStat first, with those reviewed backups.
- `--source-policy singstat`: the same retries and second pass, without backups.
- `--source-run PATH`: verify and reuse that source snapshot, with no fresh data request.

Saved-source v2 analysis requires a v2 snapshot containing outcomes. Missing outcomes are never silently downloaded into an older snapshot. Use `--report-version 1` explicitly for a legacy brief. The Python `run_workflow` API retains version 1 as its compatibility default; the CLI defaults to version 2.

## Selection and calculations

The reviewed catalogue defines identities, units, coverage and possible economic channels. Downloaded metadata must match it. Discovery does not automatically approve a new indicator or change a parser. The full pool separates the reviewed candidate rationale from the actual run's selection reason.

Quality checks use actual calendar periods, finite values, exact baselines, history, completeness and freshness. Minimum history is three annual, eight quarterly or 24 monthly observations, with at least 75% completeness inside the captured recent window. Missing periods are not repaired by counting rows backward. These are explicit engineering thresholds, not economic laws.

Version 2 adds these calculations; see [Report v2 methodology](docs/report-v2.md):

1. Calculate exact previous-quarter and year-on-year changes in three housing indices.
2. Derive vacancy as matching vacant completed units / matching completed private stock × 100. Rate changes use percentage points.
3. Transform candidates into exact year-on-year percentage, percentage-point or basis-point changes. Monthly inputs use actual March/June/September/December readings; annual inputs remain annual.
4. Compare all 16 candidates with all three outcomes at predeclared leads of 0, 1, 2 and 4 quarters, or years for annual candidates. Save sample counts, spans and skipped reasons.
5. For supported quarterly pairs, fit an expanding single-indicator ridge model to next-quarter growth, with at least 24 training pairs and eight test predictions. Compare historical mean, last observed growth and zero growth on identical dates. Save errors, direction accuracy and every prediction.

Both endpoints of statistical changes must be from 2015 Q1 onward to avoid spanning major index methodology changes. Sparse samples, annual quarterly forecasts and constant correlations are skipped. Settings are not optimized against reported test errors. The model receives exploratory correlations, but not held-out forecast errors. The histories still support many comparisons, so this is not an untouched confirmatory test or a joint model of the selected dashboard.

## Dates and historical vintages

`--as-of` is an **observation-reference cutoff**, using the captured vintage. It does not reconstruct what had been published on a past date. Population and HDB stock use verified June-end reference dates. Household-count filtering conservatively uses year-end because a consistent precise reference date was not verified; this does not imply measurement on December 31.

Reference dates, publication dates, table updates and retrieval times remain distinct. Historical revisions and release timing are not reconstructed. Walk-forward checks avoid future observation periods in training, but cannot establish that each input was published at its forecast origin. A strict publication-aware backtest would require archived releases.

## Run artifacts

| Files | Purpose |
|---|---|
| `report.md`, `report.html` | Canonical English report and formatted HTML with embedded charts |
| `indicator_pool.md`, `.html`, `.json` | All definitions, source facts, quality, decisions and limitations |
| `catalogue.json`, `discovery.json` | Run-specific candidate configuration and official discovery |
| `raw/`, `retrievals.json`, `source_routes.json` | Original responses, hashes, times, retries and final routes |
| `normalized.json`, `processed.csv`, `evaluations.json` | Captured histories, filtered observations, quality and evidence |
| `outcomes_*.json`, `outcomes_processed.csv` | Separate housing outcomes, definitions and evidence |
| `research.json`, `correlations.csv`, `walk_forward_metrics.csv` | All 48 comparisons, predictions, settings, spans and skips |
| `charts/` | SVG/PNG figures and exact plotted inputs |
| `selection.json`, `agent_trace.json` | Actual decisions and model/tool interaction; trace only for agent mode |
| `report_context.json`, `manifest.json` | Replay context, status, code hashes, usage and SHA-256 inventory |

Evidence follows calculation → evaluation input → raw locator → original response. Adapter-generated metadata is labelled separately from official bytes. The HTML renderer escapes text and embeds only images inside its run directory; external images and path traversal are refused.

## Other commands and historical evidence

```bash
python -m housing_agent discover "residential properties" --output runs/discovery
python -m housing_agent indicator-pool examples/independent_sources_run --output runs/pool-export
python -m housing_agent review-report examples/english_glm_v2_run --review-file docs/evidence/english-report-v2-editorial-review.json --output runs/reviewed-report
python -m housing_agent --help
```

Standalone pool export verifies its source run without modifying it, fetching data, selecting indicators or calling a model. It retains the source run's presentation version.

Editorial review creates a separate presentation from verified v2 artifacts, preserves original model output, labels corrected reasons, and records zero new API calls. Selected IDs, raw observations, charts and statistical results remain unchanged. Corrections are explicit English review input, not additional model output; this step is not automatic semantic validation.

The submitted presentation can be recreated in a new directory with:

```bash
python -m housing_agent review-report examples/english_glm_v2_run --review-file docs/evidence/submission-editorial-review.json --output runs/submission-review
```

The final archive is named `Yijun Li Engineering Task.zip` and contains a clean Git checkout with its history. Downloading GitHub's ordinary source ZIP omits `.git` and does not satisfy that submission requirement.

Historical audit notes and examples are preserved in their original form, including Chinese documentation. They record earlier behavior, not current results. New report v2 outputs and documentation are English. Earlier evidence includes [source verification](docs/source-evidence.md), [retry diagnosis](docs/evidence/singstat-maintenance-diagnosis.json), [GLM review](docs/glm-run-review.md) and [earlier validation](docs/validation.md).

The repository includes development history. Archives must exclude `.env`, virtual environments, caches and unrelated working directories. Raw official source content is preserved exactly rather than translated.
