# Report v2: actual run, verification and cost

## Delivered artifacts

- [Reviewed English report](../examples/english_glm_v2_reviewed_run/report.md) and [formatted HTML](../examples/english_glm_v2_reviewed_run/report.html).
- [Complete English indicator pool](../examples/english_glm_v2_reviewed_run/indicator_pool.md) and [searchable table](../examples/english_glm_v2_reviewed_run/indicator_pool.html).
- [Immutable original live-agent run](../examples/english_glm_v2_run/report.md), including its trace, original decisions and source responses.
- [Methodology](report-v2.md), [independent arithmetic audit](evidence/english-report-v2-audit.json), [editorial corrections](evidence/english-report-v2-editorial-review.json), [package verification](evidence/english-report-v2-package-verification.json) and [cost calculation](evidence/english-report-v2-cost.json).

## Fresh official capture and GLM execution

Observation cutoff: **2026-10-01**. The live run began at **2026-10-01 14:41:54 UTC**, using clean committed execution code `0955dcc026e68ff5c859d0c2fc8ed575fd60835c`.

All 16 explanatory candidates and three housing outcomes downloaded successfully from SingStat and passed their data-usability gates. There were 47 logical retrieval records, no observed maintenance response, no fallback download and no missing candidates or outcomes. Captured original histories contain 2,816 observations, including 498 housing-index observations. Data freshness refers to a new download, not a claim that every latest observation has the report date.

The model returned `zai-org/GLM-5.3`, selected five indicators, and supplied all 16 individual reasons. It retained resident unemployment, the SORA benchmark, private vacant-unit count, resident household count and median employment income among resident employed households. One empty-selection submission was rejected locally and repaired within the six-request run. No rules fallback or system-authored missing exclusion was used.

Total elapsed time was **224.542 seconds**; model interaction took **113.167208 seconds**. Eight chart pairs were generated as SVG/PNG, with exact plotted inputs. The report HTML displays all eight embedded figures and 12 tables; indicator-pool search and the selected-only filter were checked in the browser.

## Observed housing outcomes

Latest captured outcomes refer to **2026 Q2**:

| Outcome | Index | Quarter-on-quarter change | Year-on-year change |
|---|---:|---:|---:|
| Private residential prices | 219.4 | +0.5039% | +2.9081% |
| Private residential rents | 162.5 | +0.6815% | +1.6896% |
| HDB resale prices | 202.8 | −0.2950% | −0.0493% |

These are exact changes from the captured, rounded index values, not currency prices or seasonally adjusted growth. The outcomes show mixed latest quarterly directions. The matching private vacancy calculation is **26,961 / 424,581 × 100 = 6.3500%**, with changes of **+0.1831 percentage points** quarter on quarter and **−0.7968 percentage points** year on year.

## Empirical results and independent recalculation

The full grid has **48 candidate/outcome pairs** and **192 fixed-lag correlation records**: 174 computed and 18 explicitly skipped. Quarterly prediction checks evaluated 24 pairs and skipped 24 because annual interpolation or minimum-history requirements were not supported.

For the selected dashboard, nine quarterly pairs support prediction checks. The single-indicator ridge model beat historical-mean MAE in four pairs, last-growth MAE in three, and zero-growth MAE in eight. It beat **all three baselines in only one pair**. These results do not validate the selected set as a joint forecasting model.

Independent verification checked:

- 87 inventoried source-run artifacts and all 2,816 original SingStat cell values/periods.
- 29 latest changes using Decimal arithmetic.
- All 174 computed correlations using independent NumPy correlation calculations.
- All 408 ridge predictions using independent matrix solves and chronological checks.
- 288 metric values and 154 matching-quarter vacancy rates.
- English presentation in the report and pool's five human-facing files.

Maximum absolute differences were below **5 × 10⁻¹¹** for changes, correlations and metrics; ridge predictions differed by at most **3.82 × 10⁻¹⁴**. The independent audit can be rerun with:

```bash
python scripts/audit_report_v2.py examples/english_glm_v2_run --output runs/new-audit.json
```

The script needs NumPy, available with the charts extra, and never edits the captured run.

## Editorial corrections and software verification

The automated checks accepted structurally valid model prose, but review found unsupported scope claims. Six reasons were corrected: per-employed-person income, aggregate disposable income, total pipeline, total employment, employed-household median income and HDB stock. Three narrative fields were clarified. Corrections remove claims that the pipeline is unpurchased, that most employed pass holders receive employer-arranged housing, or that GDP correlation/typical-buyer coverage was established.

The original model output remains immutable. The reviewed report labels corrected reasons as editorial review and preserves `original_selection.json`. Its 80 unchanged source, chart, trace and research artifacts retain the original hashes; review used **zero** model or source calls.

**254 automated tests passed.** A built wheel was installed without dependencies into an isolated environment outside the repository. It contained the three outcome configurations. All **10** saved reports, including the original and reviewed v2 reports, replayed exactly without OpenAI SDK, Matplotlib, credentials, source calls or model calls.

## Actual token usage and price estimate

| Item | Returned usage |
|---|---:|
| Requests | 6 |
| Input tokens | 156,787 |
| Cached input subset | 109,248 |
| Output tokens | 8,869 |
| Reasoning output subset | 5,104 |
| Total tokens | 165,656 |

The [official mainland price page](https://www.siliconflow.cn/pricing), checked on 2026-10-01 and confirmed by the [GLM-5.3 announcement](https://siliconflow.cn/news/is96b67809iqvyxrumd90q7x), lists CNY 8 per million uncached input tokens, CNY 2 cached input, and CNY 28 output.

Estimate: `(156787 − 109248) × 8 / 1000000 + 109248 × 2 / 1000000 + 8869 × 28 / 1000000 = CNY 0.847140`. Cache and reasoning counts are subsets; neither is added again. Thirty runs at identical usage would estimate **CNY 25.4142**. This is a published-price calculation, not an observed account debit or a guaranteed future budget. Repairs, cache behavior, model changes and failures can alter cost.

## Remaining research limits

This completes report presentation, outcome measurement and bounded empirical checks. It does not complete publication-aware historical-vintage validation, an untouched confirmatory test or a justified joint forecasting model. Revisions and historical release timing remain unresolved. Qualitative model reasons still require review; automated numeric/evidence validation is not semantic proof.
