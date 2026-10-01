# Initial implementation contract

Python 3.11+, standard library for data/replay/tests; optional `openai` for live model calls. Plain JSON dictionaries cross module boundaries. Root implements sources, catalogue mapping, runner/CLI and reporting. Other owners implement only assigned modules and tests.

## Normalized series

`id`, `name`, `theme`, `definition`, `unit`, `frequency` (`A`, `Q`, `M`), `update_frequency` (honest source statement or unavailable), `source_url`, `table_id`, `row_id`, `source_agency`, `retrieved_at`, `source_updated_at`, `provenance` (raw_file, raw_sha256, metadata_file, metadata_sha256), `mechanism` ({sales, rents, lag, limitations}), `observations`.

Each observation: `period` (YYYY, YYYY-Qn, YYYY-MM), `value` (finite number or null), `raw_period`, `raw_value`, `raw_index` (index within selected row's columns). `published_at` optional ISO date if actually known. Do not invent publication dates from table-level update dates. `change_kind` is `percent`, `percentage_point`, `basis_point`, or `absolute`; rate levels stored in percentage units. `scope` and `seasonal_adjustment` are optional metadata.

## Engine interface

`evaluate_series(series: dict, as_of: str) -> dict`, no network. Return keys `id`, `metadata` (all original fields except observations), `latest` (observation or null), `changes` (list), `quality` ({eligible: bool, score: float, reasons: list[str], warnings: list[str], missing_fraction: float, valid_count: int}), `observations` (filtered canonical observations <= as_of, retained for audit). `as_of` period cutoff uses period END, latest-vintage semantics explicitly disclosed, never claims historical availability. Unsupported freq/schema/duplicates raise ValueError caught by runner and recorded.

Change keys: `id` (series id + ':' + comparison), `comparison` (previous_period or year_on_year), `value` (number or null), `unit`, `latest_period`, `latest_value`, `base_period`, `base_value`, `formula`, `reason` (null or inability explanation), `evidence` (list of exact observation dicts used). Locate baselines by actual calendar keys, never positional shifts. For A only year_on_year. Preserve rates in pp or bp as configured. A metric id remains stable.

`select_candidates(evaluations: list[dict], limit: int = 5) -> dict`: data-quality and theme-diversity selection, not fixed indicators and not claimed predictive validation. Return `selected_ids`, `decisions` list of {id, selected: bool, reason}, `method`. Never fill quota with ineligible candidates. Deterministic ordering/ties. Caller may ask LLM to propose selection from eligible records.

## LLM interface

`run_agent(evaluations: list[dict], as_of: str, limit: int, model: str, trace_path: pathlib.Path, max_turns: int = 8, max_output_tokens: int = 4000) -> dict` returns `selected_ids`, `decisions` (all candidates, include exclusions), `narratives` (mapping id -> {sales, rents, lag, limitations, evidence_ids: list[str]}), `method`, `usage`. Uses optional OpenAI import inside function and environmental OPENAI_API_KEY; missing key must explicitly fail. Root provides deterministic rule-mode fallback as explicit CLI mode, never silently labels it LLM. Require nonnumeric qualitative prose (numbers inserted by report from facts); evidence IDs must match latest/changes from selected records. Detect suspicious numeric unsupported narrative; no forecast or causal certainty claims. Record actual tool call/response and output validation details, exclude secrets. Use OpenAI Responses function calling documented at https://developers.openai.com/api/docs/guides/function-calling . Do not execute model-provided code or network URLs. Configurable provider-specific model and local credentials; actual live integration status is recorded in docs/validation.md.

## Delivery and scope

CLI `python -m housing_agent run --as-of YYYY-MM-DD --mode rules|llm --output runs/NAME`, `replay RUN_DIR --output REPORT.md`, `discover QUERY`. Exact command implementation owned by root. Every run stores immutable raw snapshots, normalized data, evaluations, selection, generated narrative, report, manifest with checksums. No automatic scheduler/site; scope is date-driven CLI. Reports English for take-home reviewers; README bilingual or Chinese quick start. Keep claims and source metadata honest; real data can only come from captured official responses.

## Source routing revision

All sixteen reviewed candidates use SingStat first. Each transient request receives at most three attempts; failures never block independent candidates. Retryable candidate failures receive a later second pass before any reviewed per-candidate MOM/MAS backup. Schema/permanent failures are not blindly retried. The strict SingStat policy has the same retries without backups. Source routes and bounded error-response prefixes are retained with hashes; a single maintenance response is not a site-wide health verdict.
