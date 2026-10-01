# English report v2: implementation and methodology

Version 2 replaces the indicator brief with a structured English research report. The CLI defaults to v2; Python callers opt in with `report_version=2`. Version 1 rendering remains available to replay immutable historical examples exactly.

## Completed report features

- An executive summary reports observed market movements before possible explanatory channels.
- Three quarterly housing indices are retrieved separately from the 16 explanatory candidates.
- Charts show index levels, quarterly growth, private vacancy and every selected indicator at its original frequency. SVG, PNG and exact plotted inputs are saved; HTML embeds the SVGs.
- Vacancy uses its matching stock denominator even if stock is excluded from the selected dashboard.
- Every candidate receives an individual English decision. Agent mode rejects omissions and uninspected candidates instead of inserting system-authored reasons.
- The full English pool records definitions, reviewed rationale, captured sources, quality, actual decisions and limitations.
- Every candidate/outcome pair receives fixed lead/lag correlations and supported retrospective prediction checks against baselines.
- Inputs, formulas, skipped reasons, test dates and predictions remain auditable and replayable offline.

## Outcomes and coverage

| Outcome | Official row | Definition and method |
|---|---|---|
| Private residential property price index | [M212261:1](https://tablebuilder.singstat.gov.sg/table/TS/M212261), Residential Properties | URA overall private sale-price index; 2009 Q1 = 100. Stratified hedonic method from 2015 Q1. |
| Private residential rental index | [M212311:1](https://tablebuilder.singstat.gov.sg/table/TS/M212311), Rental Index Of Residential Properties | URA overall private rental index; 2009 Q1 = 100. Stratified hedonic method from 2015 Q1. |
| HDB resale price index | [M212161:1](https://tablebuilder.singstat.gov.sg/table/TS/M212161), HDB Resale Price Index | Public-housing resale outcome; 2009 Q1 = 100. Stratified hedonic method from 2014 Q4. |

URA's [coverage and methodology](https://eservice.ura.gov.sg/reis/coverageandMethodology) distinguishes sale and rental coverage. Private sales exclude HDB and other public-sector buildings; non-landed prices include executive condominiums more than ten years old. Rental coverage includes executive condominiums, whereas private stock/vacancy excludes them. Equal index bases do not imply equal market universes.

The HDB table documents rescaling earlier history by 100/138.3 and possible rounding differences. Statistical changes require both endpoints from 2015 Q1 onward. Earlier captures remain available for audit. Descriptive changes use exact previous-quarter or prior-year quarters, not adjacent rows. Index levels are not dollar prices and no seasonally adjusted growth is implied.

## Calendar alignment

Explanatory features use exact year-on-year changes: `(current/base - 1) × 100`, a level difference in percentage points, or a rate difference multiplied by 100 to obtain basis points.

- Quarterly features retain actual quarters.
- Monthly features use only March, June, September and December. Missing endpoints remain missing; no averaging or nearest-month substitution is applied.
- Annual features remain annual and are compared with same-year Q4 year-on-year outcome growth. Leads are in years. No quarterly prediction sample is synthesized from annual data.

Quarterly associations compare candidate year-on-year changes with quarter-on-quarter outcome growth. Pearson leads are fixed at 0, 1, 2 and 4 quarters; positive lead means the candidate precedes the outcome. At least eight paired values and nonconstant series are required. Paired counts and outcome spans are saved. There is no significance claim or multiple-comparison adjustment.

## Retrospective walk-forward checks

Each supported pair predicts next-quarter index growth from the candidate's current year-on-year change. This is a **single-indicator benchmark**, not a fitted joint model of the selected five indicators.

At least 24 matched pairs form the initial training sample, followed by at least eight test predictions. Training expands at each origin; its targets must end no later than that origin. Mean and population standard deviation are fitted on training rows only. Ridge penalty is fixed at 1 and the intercept is unpenalized. A constant feature becomes a historical-mean prediction.

Four methods are scored on identical dates: single-indicator ridge, expanding training-target mean, last observed quarter's growth, and zero growth. MAE/RMSE are percentage-point errors in growth. Direction accuracy distinguishes positive, negative and zero; absolute values within 1e-12 count as zero. Different histories can yield different test windows, so smaller errors across different windows do not establish an overall ranking.

All 16 × 3 = 48 pairs are retained. Annual candidates, short histories, missing sources and invalid fits produce explicit skipped records. Report tables show selected indicators; JSON and CSV files preserve the full grid and every prediction. The selecting agent sees exploratory correlations, not held-out error metrics.

## Remaining limits

Sources use the latest captured vintage. Historical release dates and revisions are not reconstructed. Avoiding future observation periods therefore cannot prove that inputs were published at their prediction origins. A strict historical-vintage test needs archived releases and publication dates.

The histories support many exploratory comparisons and are not an untouched confirmatory sample. Neither a large correlation nor a baseline improvement establishes causality, robust forecasting ability, optimality or an investment recommendation. Further validation needs publication-aware vintages, an independent evaluation period and justified joint-model comparisons.

Model reasons remain qualitative judgements. Main-page numeric values and signal directions are deterministic; syntax/evidence validation cannot verify every economic statement. Population and household stocks do not identify majority tenure or gross household formation.

## Reproducibility

Runs are immutable directories with SHA-256 inventories. Replay validates files and regenerates Markdown without Matplotlib, keys, source requests or model calls. Saved-source v2 analysis requires captured outcomes and never mixes a fresh outcome download into an old snapshot.

Fresh source errors remain independent and receive bounded retries. Unavailable outcomes create explicit omissions and skipped checks, never fabricated values. Charts are optional for generation; core replay is dependency-free. HTML escapes source text and rejects external images, traversal and symlinks outside its asset directory.
