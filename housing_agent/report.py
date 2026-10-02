"""Deterministic report rendering: numeric facts never come from free-form LLM text."""
from __future__ import annotations

import html
import base64
import math
import re
from pathlib import Path
from urllib.parse import urlsplit


def fmt(value) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, (int, float)):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_report_v1(run: dict, evaluations: list[dict], selection: dict) -> str:
    selected = set(selection["selected_ids"])
    chosen = [x for identifier in selection["selected_ids"] for x in evaluations if x["id"] == identifier]
    output = [
        "# Singapore housing: macroeconomic research brief", "",
        f"**Reporting date:** {run['as_of']}  ", f"**Run:** `{run['run_id']}`  ",
        f"**Generated at:** {run['created_at']}  ",
        f"**Analysis mode:** {run['mode_label']}  ",
        f"**Data basis:** {run['data_basis']}", "",
        "> This is a study of possible indicators, not a price forecast or evidence of causation. "
        "The reporting date filters observation dates; the values are from the latest downloaded vintage. "
        "Observation-level release dates and historical revisions are generally unavailable. "
        "This report does not recreate the information set known on the reporting date.", "",
        "## Candidate selection", "",
        f"Evaluated {len(evaluations)} candidates and selected {len(chosen)}. {selection['method']}", "",
        "Quality scores describe data usability, not predictive strength. The candidate universe is bounded by a reviewed "
        "catalogue; live official catalogue search is saved separately. Final inclusion changes with actual data quality "
        "and the reporting date. Predictive validation against housing outcomes is not performed in this first version.", "",
        "| Candidate | Theme | Latest usable period | Quality score | Decision | Reason |",
        "|---|---|---|---:|---|---|",
    ]
    decisions = {d["id"]: d for d in selection["decisions"]}
    if run.get("source_routing_version"):
        output[-2:-2] = [f"**Source strategy:** {run['source_strategy']}. "
                        "Per-candidate attempts and actual routes are recorded in [source_routes.json](source_routes.json).", ""]
    if run.get("indicator_pool_files"):
        # Optional marker keeps every earlier immutable sample byte-replayable.
        output[-2:-2] = ["[完整指标池表：定义、纳入理由、官方来源和本次选择](indicator_pool.md) · "
                        "[可搜索的表格预览](indicator_pool.html)", ""]
    for item in evaluations:
        meta = item["metadata"]
        dec = decisions.get(item["id"], {"reason": "Not selected"})
        output.append("| " + " | ".join(map(cell, [
            f"{meta.get('name', item['id'])} ({item['id']})", meta.get("theme", "unknown"),
            (item.get("latest") or {}).get("period", "Unavailable"), fmt(item["quality"]["score"]),
            "Selected" if item["id"] in selected else "Excluded", dec["reason"],
        ])) + " |")
    for item in chosen:
        meta, latest = item["metadata"], item["latest"]
        output += ["", f"## {meta['name']}", "",
            f"- **Series:** `{item['id']}`; **Theme:** {meta['theme']}",
            f"- **Source:** {meta['source_agency']} via [{meta.get('source_provider', 'SingStat Table Builder')}]({meta['source_url']})",
            f"- **Definition:** {meta['definition']}", f"- **Coverage:** {meta.get('scope', 'See source')}",
            f"- **Unit:** {meta['unit']}; **Observation frequency:** {meta['frequency']}; **Seasonal adjustment:** {meta.get('seasonal_adjustment', 'Not established')}",
            f"- **Update frequency:** {meta['update_frequency']}",
            f"- **Latest usable observation:** {fmt(latest['value'])} {meta['unit']} in {latest['period']} (evidence `{item['id']}:latest`)",
            f"- **Observation reference date:** {latest.get('observation_date', 'Period end used conservatively')}",
            f"- **Source table last updated:** {meta.get('source_updated_at') or 'Not supplied'}; **Retrieved:** {meta['retrieved_at']}",
            "", "| Comparison | Latest period | Base period | Change | Unit | Evidence |",
            "|---|---|---|---:|---|---|",
        ]
        for change in item["changes"]:
            output.append("| " + " | ".join(map(cell, [change["comparison"], change["latest_period"], change["base_period"], fmt(change["value"]), change["unit"], change["id"]])) + " |")
        for change in item["changes"]:
            if change.get("reason"):
                output.append(f"\nCalculation limitation: {change['reason']}\n")
        narrative = selection.get("narratives", {}).get(item["id"], meta["mechanism"])
        output += ["", f"**Possible sales-market channel:** {narrative['sales']}", "",
                   f"**Possible rental-market channel:** {narrative['rents']}", "",
                   f"**Possible lag:** {narrative['lag']}", "", f"**Limitations:** {narrative['limitations']}", ""]
        if narrative.get("evidence_ids"):
            output.append("Referenced evidence: " + ", ".join(f"`{x}`" for x in narrative["evidence_ids"]) + ".")
        for warning in item["quality"].get("warnings", []):
            output.append(f"- Data warning: {warning}")
        if meta.get("transformation_note"):
            output.append(f"- Source transformation: {meta['transformation_note']}")
        if latest.get("preliminary"):
            output.append("- Data warning: the latest observation is marked preliminary by the official source.")
        provenance = meta["provenance"]
        if meta.get("source_provider"):
            trace_note = (f"Reviewed catalogue identity: `{item['id']}`. Actual source location for the latest value: "
                          f"`{latest.get('raw_locator', latest.get('raw_index'))}`. "
                          "The observations retain original labels, values and file locations; "
                          "monthly samples also retain their source daily dates. "
                          f"Adapter-generated definition and transformation notes: `{provenance['metadata_file']}` "
                          f"(SHA-256 `{provenance['metadata_sha256']}`); this is not an official API metadata response. "
                          "Each calculated change retains the formula and both input observations.")
        else:
            trace_note = (f"Exact source row: `{meta['row_id']}` in table `{meta['table_id']}`. "
                          "The observations in `evaluations.json` retain original period, value and raw column index. "
                          "Each calculated change retains the formula and both input observations.")
        output += ["", "<details><summary>Trace the numbers</summary>", "",
            f"Raw response: `{provenance['raw_file']}`; SHA-256 `{provenance['raw_sha256']}`.", "",
            trace_note, "",
        ]
        for change in item["changes"]:
            output.append(f"- `{change['id']}`: `{change['formula']}`; inputs {fmt(change['latest_value'])} and {fmt(change['base_value'])}.")
        if meta.get("row_footnote"):
            output += ["", "Source row note: " + meta["row_footnote"]]
        if meta.get("source_provider") and meta.get("source_footnote") and meta["source_footnote"] != meta.get("row_footnote"):
            output += ["", "Source file notes: " + meta["source_footnote"]]
        output += ["", "</details>"]
    output += ["", "## Run limitations and reproducibility", ""]
    for warning in run.get("warnings", []):
        output.append(f"- {warning}")
    output += [
        "- Mixed observation frequencies are preserved; annual data are not interpolated to months.",
        "- Private residential series retain their own coverage and are not automatically generalised to HDB housing.",
        "- Qualitative mechanisms are research hypotheses. A market forecast would require an explicit outcome, vintage-aware validation and held-out evaluation.",
        "- Regenerate the saved report with the replay command in the README. Replay verifies file hashes and reuses saved facts and narratives without data or model calls.",
        "- Refreshing sources creates a different run; source revisions can change results. Raw snapshots are never silently overwritten.", "",
    ]
    return "\n".join(output)


def _render_html_v1(markdown: str) -> str:
    # A dependency-free, searchable preview of the exact report; Markdown remains canonical.
    pool_link = ('<p><a href="indicator_pool.html">查看完整指标池表 · 定义、选择理由和官方来源</a></p>'
                 if "[可搜索的表格预览](indicator_pool.html)" in markdown else "")
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Housing research brief</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;background:#f6f7f9;color:#172033;font:16px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #dbe1e8;padding:28px;border-radius:12px;font:inherit}</style><body>' + pool_link + '<pre>' + html.escape(markdown) + '</pre></body></html>'


_V2_MARKER = '<!-- housing-report-version: 2 -->'
_FREQUENCIES = {'A': 'Annual', 'Q': 'Quarterly', 'M': 'Monthly'}


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _signed(value):
    return ('+' if value > 0 else '') + fmt(value) if _number(value) else 'Not available'


def _change(item, comparison):
    return next((x for x in item.get('changes', []) if x.get('comparison') == comparison), {})


def _change_text(change):
    if not _number(change.get('value')):
        return 'Not available' + (': ' + change['reason'] if change.get('reason') else '')
    text = f"{_signed(change['value'])} {change.get('unit', '%')}"
    if change.get('base_period'):
        text += f" vs {change['base_period']}"
    return text


def _table(headers, rows):
    return ['| ' + ' | '.join(map(cell, headers)) + ' |',
            '|' + '|'.join('---' for _ in headers) + '|'] + [
            '| ' + ' | '.join(map(cell, row)) + ' |' for row in rows]


def _safe_relative_path(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_./-]+', value):
        return None
    path = Path(value)
    if path.is_absolute() or any(part in ('..', '.') for part in value.split('/')):
        return None
    return value


def _source_link(item):
    meta = item.get('metadata', item)
    url = meta.get('source_url') or item.get('source_url')
    agency = meta.get('source_agency') or item.get('source_agency') or 'Official source'
    return f'[{agency}]({url})' if url and _safe_url(url) else agency


def _signal_reading(item, research):
    """Qualitative direction from supplied, calculated facts; never LLM numbers."""
    change = _change(item, 'year_on_year')
    if not _number(change.get('value')):
        return 'No permitted year-on-year comparison is available; direction is not inferred.'
    value = change['value']
    direction = 'rose' if value > 0 else 'fell' if value < 0 else 'was unchanged'
    prefix = f"The reading {direction} year on year. "
    theme = item['metadata'].get('theme')
    if theme == 'financing_cost':
        effect = 'raise' if value > 0 else 'ease' if value < 0 else 'leave unchanged'
        return prefix + f'This may {effect} the benchmark component of financing costs as loans reset; mortgage spreads and the rent response remain uncertain.'
    if item['id'] == 'M182342:2':
        return prefix + ('Higher unemployment may weigh on resident purchasing capacity and rent affordability.' if value > 0 else
                         'Lower unemployment may support resident purchasing capacity and rent affordability.' if value < 0 else
                         'This comparison shows no change in resident unemployment stress.')
    if theme in ('household_income',):
        return prefix + 'This is nominal affordability context; scope, inflation, CPF treatment and household composition limit any take-home purchasing-power inference.'
    if theme == 'population_demand':
        return prefix + 'This supplies structural demand context, conditional on tenure and affordability; population or household-stock changes do not identify gross household formation.'
    if theme == 'vacant_supply':
        vacancy = research.get('derived_private_vacancy_rate', {})
        rate_change = _change(vacancy, 'year_on_year')
        if _number(rate_change.get('value')):
            rate_direction = 'rose' if rate_change['value'] > 0 else 'fell' if rate_change['value'] < 0 else 'was unchanged'
            return prefix + f'The separately derived vacancy rate {rate_direction} year on year; read the count with this matching-stock denominator. Vacancy does not establish active rental listings.'
        return prefix + 'A count alone does not establish market tightness; the matching completed-stock denominator is required, and vacant units need not be listed for rent.'
    if theme in ('completed_supply', 'public_housing_supply'):
        return prefix + 'Completed dwelling stock is supply context, not the flow of completions or a count of homes actively offered for sale or rent.'
    if theme == 'future_supply':
        return prefix + 'Pipeline changes can affect expectations, but development timing and cancellations prevent interpreting the total as a completion forecast.'
    if theme == 'housing_credit':
        return prefix + 'Outstanding credit is not new lending or credit availability; repayments and housing-market activity can both move the stock.'
    if theme == 'economic_activity':
        return prefix + 'Economic activity may affect jobs, income and confidence; this is a possible channel, not a quantified housing-price effect.'
    if theme == 'employment_level':
        return prefix + 'Employment supports demand context but includes workers whose accommodation is not a separate market rental.'
    if theme == 'inflation':
        return prefix + 'Consumer-price movements affect real budgets; housing components overlap with rents and the net property-price effect is uncertain.'
    return prefix + 'An association with housing outcomes requires separate testing.'


def _outcome_sentence(outcome):
    latest = outcome.get('latest') or {}
    if not _number(latest.get('value')):
        return f"{outcome.get('name', outcome['id'])}: unavailable. {outcome.get('reason') or 'No usable observation was supplied.'}"
    comparisons = '; '.join(label + ': ' + _change_text(_change(outcome, key)) for label, key in
                            [('quarter on quarter', 'previous_period'), ('year on year', 'year_on_year')])
    return f"{outcome.get('name', outcome['id'])}: {fmt(latest['value'])} {outcome.get('unit', 'index points')} in {latest.get('period', 'unknown period')}; {comparisons}."


def _correlation_cell(row):
    if not row or not _number(row.get('pearson_r')):
        return 'Not estimable' + (f" (n={row.get('n', 0)})" if row else '') + (': ' + row['reason'] if row and row.get('reason') else '')
    return f"{row['pearson_r']:.3f} (n={row.get('n', 'unknown')})"


def _chart_lines(charts):
    output = []
    for chart in charts:
        path = _safe_relative_path(chart.get('path'))
        if path:
            output += ['', f"![{chart.get('title', 'Historical chart')}]({path})"]
            if chart.get('caption'):
                output += ['', chart['caption']]
    return output


def _benchmark_reading(comparisons):
    tested = [x['walk_forward']['metrics'] for x in comparisons
              if x.get('walk_forward', {}).get('status') == 'evaluated']
    if not tested:
        return 'No selected indicator/outcome pair supports the minimum quarterly walk-forward sample; no predictive improvement is claimed.'
    wins = {baseline: sum(m['ridge']['mae'] < m[baseline]['mae'] for m in tested)
            for baseline in ('historical_mean', 'last_change', 'zero_change')}
    all_wins = sum(all(m['ridge']['mae'] < m[b]['mae'] for b in wins) for m in tested)
    return (f"Across {len(tested)} evaluated selected indicator/outcome pairs, the single-indicator ridge model has lower holdout MAE than "
            f"historical mean in {wins['historical_mean']}, last observed growth in {wins['last_change']}, and zero growth in {wins['zero_change']}. "
            f"It beats all three on {all_wins} {'pair' if all_wins == 1 else 'pairs'}. Each comparison uses its own matching test dates; these counts do not validate the selected dashboard as a joint forecasting model.")


def _quality_label(item, enhanced):
    if enhanced and (not item.get('latest') or not item.get('observations')
                     or not item.get('metadata', {}).get('provenance', {}).get('raw_file')):
        return 'Not assessed'
    return fmt(item['quality'].get('score'))


def _narrative_lines(run, item, selection):
    """Preserve saved wording and identify editorial changes at field level."""
    saved = selection.get('narratives', {}).get(item['id'], {})
    mechanism = item['metadata'].get('mechanism', {})
    edits = selection.get('editorial_review', {}).get('narrative_edits', {}).get(item['id'], {})
    output = []
    for field, label in [('sales', 'Possible sales-market channel'), ('rents', 'Possible rental-market channel'),
                         ('lag', 'Possible economic response lag'), ('limitations', 'Limitations')]:
        wording = saved.get(field)
        if wording:
            if field in edits:
                source = 'Editorial review; see the [review record](selection_review.json) and [original selection](original_selection.json).'
            elif run.get('mode') == 'llm':
                source = 'Original model narrative; numerical checks do not establish the correctness of this interpretation.'
            elif run.get('mode') == 'rules':
                source = 'Reviewed catalogue mechanism, used by deterministic rules; no model wording.'
            else:
                source = 'Saved narrative; author not recorded.'
        elif mechanism.get(field):
            wording = mechanism[field]
            source = 'Reviewed catalogue mechanism used as a fallback; no model wording.'
        else:
            wording = 'Not supplied.'
            source = 'No narrative supplied.'
        output += [f'**{label}:** {wording}', '', f'Wording source: {source}', '']
    if saved.get('evidence_ids'):
        output += ['Referenced evidence: ' + ', '.join(f'`{value}`' for value in saved['evidence_ids']) + '.', '']
    return output


def _render_report_v2(run, evaluations, selection, research):
    enhanced = run.get('report_fields_version', 1) == 2
    by_id = {x['id']: x for x in evaluations}
    chosen = [by_id[sid] for sid in selection['selected_ids'] if sid in by_id]
    outcomes = research.get('outcomes', [])
    outcome_names = {x['id']: x.get('name', x['id']) for x in outcomes}
    candidates = {x['id']: x for x in research.get('candidates', [])}
    chosen_ids = {x['id'] for x in chosen}
    comparisons = [x for x in research.get('comparisons', []) if x.get('candidate_id') in chosen_ids]
    output = [_V2_MARKER, '# Singapore housing market research report', '',
              f"**Reporting date:** {run['as_of']}  ", f"**Run:** `{run['run_id']}`  ",
              f"**Generated at:** {run['created_at']}  ", f"**Analysis mode:** {run['mode_label']}", '',
              f"**Data basis:** {run['data_basis']}", '',
              '## Executive summary', '']
    if outcomes:
        output += ['- ' + _outcome_sentence(x) for x in outcomes]
    else:
        output += ['- Housing outcome data were not supplied; this report cannot establish actual price or rent movements.']
    output += ['', f"The selected dashboard contains {len(chosen)} of {len(evaluations)} evaluated indicators. "
               'It combines observed indicator changes with explicitly bounded empirical checks; selection is not a claim that these are the best predictors.', '']
    output += [_benchmark_reading(comparisons), '']
    valid_moves = [_change(x, 'previous_period').get('value') for x in outcomes]
    valid_moves = [x for x in valid_moves if _number(x)]
    if valid_moves:
        if all(x > 0 for x in valid_moves):
            interpretation = 'All available latest quarter-on-quarter outcome comparisons are positive.'
        elif all(x < 0 for x in valid_moves):
            interpretation = 'All available latest quarter-on-quarter outcome comparisons are negative.'
        elif all(x == 0 for x in valid_moves):
            interpretation = 'All available latest quarter-on-quarter outcome comparisons are unchanged.'
        else:
            interpretation = 'The available latest quarter-on-quarter outcome comparisons show mixed directions.'
        output += [interpretation + ' Each series retains its own reference period and market coverage; this does not establish a common cause or the next quarter\'s direction.', '']
    model_count = sum(d.get('reason_origin') == 'system' for d in selection.get('decisions', []))
    if model_count:
        output += [f"**Selection completeness:** {model_count} exclusion reason(s) were supplied by the system because the model omitted them. They are labelled in the appendix.", '']
    review = run.get('editorial_review')
    if review:
        output += [f"**Editorial review:** {review['summary']} "
                   f"{review['decision_edits']} selection reasons were corrected and are labelled editorial_review. "
                   "[Review record](selection_review.json) and [original model selection](original_selection.json) preserve the distinction. "
                   "Values, selected indicators, source captures and statistical results are unchanged; this presentation makes no new API calls.", '']
    output += ['## Market outcomes', '',
               'These official outcome series describe observed markets. Index levels are not currency prices and different indices should not be compared by their numeric levels.', '']
    output += _table(['Outcome', 'Reference period', 'Latest index', 'Quarter on quarter', 'Year on year', 'Source'], [
        [x.get('name', x['id']), (x.get('latest') or {}).get('period', 'Unavailable'),
         fmt((x.get('latest') or {}).get('value')) + ' ' + x.get('unit', ''),
         _change_text(_change(x, 'previous_period')), _change_text(_change(x, 'year_on_year')), _source_link(x)] for x in outcomes])
    for outcome in outcomes:
        if outcome.get('reason'):
            output += ['', f"{outcome.get('name', outcome['id'])}: {outcome['reason']}"]
    charts = research.get('charts', [])
    if isinstance(charts, dict):
        charts = [{'title': key.replace('_', ' ').title(), 'path': value} if isinstance(value, str) else value for key, value in charts.items()]
    charts = [{'path': chart, 'title': 'Historical outcome index'} if isinstance(chart, str) else chart for chart in charts]
    output += _chart_lines([c for c in charts if not c.get('path', '').startswith('charts/indicator_')
                            and 'private_vacancy_rate' not in c.get('path', '')])
    if not charts:
        output += ['', 'No trend chart was supplied for this run.']
    output += ['', '## Selected signals', '',
               'Reference periods remain explicit: annual, quarterly and monthly observations are not silently treated as simultaneous.', '']
    output += _table(['Indicator', 'Reference period', 'Latest value', 'Previous period', 'Year on year'], [
        [x['metadata']['name'], (x.get('latest') or {}).get('period', 'Unavailable'),
         fmt((x.get('latest') or {}).get('value')) + ' ' + x['metadata']['unit'],
         _change_text(_change(x, 'previous_period')), _change_text(_change(x, 'year_on_year'))] for x in chosen])
    output += ['', '### What the observed signals may mean', '']
    for item in chosen:
        output += [f"- **{item['metadata']['name']}:** {_signal_reading(item, research)}"]
    output += _chart_lines([c for c in charts if c.get('path', '').startswith('charts/indicator_')])
    vacancy = research.get('derived_private_vacancy_rate', {})
    output += ['', '### Vacancy with its denominator', '']
    if _number((vacancy.get('latest') or {}).get('value')):
        latest = vacancy['latest']
        output += [f"The derived private residential vacancy rate is **{fmt(latest['value'])} {vacancy.get('unit', '%')}** in **{latest.get('period', 'unknown period')}**. "
                   'It is calculated from matching vacant-unit and completed-stock observations, whether or not the denominator was retained in the selected dashboard.', '']
        output += _table(['Comparison', 'Change', 'Base period'], [[x.get('comparison', '').replace('_', ' '),
                            _signed(x.get('value')) + ' ' + x.get('unit', ''), x.get('base_period', '')] for x in vacancy.get('changes', [])])
        output += ['', 'Vacancy is unused completed stock, not a count of homes actively listed for letting. Public housing is outside this private-sector denominator.']
    else:
        output += ['A matching-stock vacancy rate is not available. ' + (vacancy.get('reason') or 'The report therefore does not infer normalized market tightness from the vacant-unit count alone.')]
    output += _chart_lines([c for c in charts if 'private_vacancy_rate' in c.get('path', '')])
    output += ['', '## Empirical checks', '',
               'These calculations are exploratory evidence, not causal proof or a validated investment strategy. '
               'Results below cover the selected indicators; the saved research data include the full evaluated set.', '',
               'The statistical window starts in **2015 Q1** to avoid spanning the major index methodology changes. '
               'Both the current and baseline observations used in a change must fall inside this window. '
               'All 16 candidates are compared with all three outcomes, including skipped results. No lag is chosen by its best observed correlation.', '',
               '### Lead and lag correlations', '',
               'A positive lag means the indicator precedes the housing outcome. Quarterly comparisons use quarterly outcome growth; annual comparisons use annual indicator changes and fourth-quarter year-on-year outcome growth. '
               'Annual rows are not interpolated into quarterly observations. Pearson correlation measures a linear association, and the number of paired observations is shown for every lag. Multiple comparisons can produce chance patterns.', '']
    corr_rows = []
    for comparison in comparisons:
        rows = comparison.get('correlations', [])
        by_lag = {x.get('lag'): x for x in rows}
        lag_unit = next((x.get('lag_unit') for x in rows if x.get('lag_unit')), comparison.get('analysis_frequency', 'periods'))
        zero = by_lag.get(0, {})
        span = f"{zero['start_period']} to {zero['end_period']}" if zero.get('start_period') else 'No paired periods'
        corr_rows.append([by_id[comparison['candidate_id']]['metadata']['name'], outcome_names.get(comparison['outcome_id'], comparison['outcome_id']),
                          lag_unit, span] + [_correlation_cell(by_lag.get(lag)) for lag in (0, 1, 2, 4)])
    output += _table(['Indicator', 'Outcome', 'Lag units', 'Lag 0 outcome span', 'Lag 0', 'Lag 1', 'Lag 2', 'Lag 4'], corr_rows)
    if not comparisons:
        output += ['', 'No aligned indicator/outcome comparisons were supplied.']
    output += ['', '### Walk-forward prediction checks', '',
               'Each single-indicator model predicts next-quarter index growth from the indicator\'s current year-on-year change. '
               'It starts with at least **24 training pairs** and requires at least **eight subsequent test predictions**. '
               'Training expands one observation at a time. Standardization uses the training sample only; ridge penalty is fixed at one and the intercept is unpenalized. '
               'Annual candidates and short histories are explicitly skipped.', '',
               'The ridge model is compared with simple baselines on the same held-out periods: historical mean growth, last observed growth and zero growth. '
               'MAE and RMSE are percentage-point errors in quarterly growth; lower is better. Direction accuracy uses negative, zero and positive changes. '
               'These are retrospective tests using the captured data vintage, not a reconstruction of releases available at each prediction date. '
               'Test windows can differ between indicators, so error magnitudes across different windows do not establish an overall ranking.', '',
               _benchmark_reading(comparisons), '']
    metric_rows, skipped = [], []
    for comparison in comparisons:
        name = by_id[comparison['candidate_id']]['metadata']['name']
        outcome = outcome_names.get(comparison['outcome_id'], comparison['outcome_id'])
        walk = comparison.get('walk_forward') or {}
        metrics = walk.get('metrics') or {}
        if not metrics:
            skipped.append([name, outcome, walk.get('reason') or 'No usable held-out evaluation was supplied.'])
            continue
        for method in ('ridge', 'historical_mean', 'last_change', 'zero_change'):
            metric = metrics.get(method)
            if not metric:
                continue
            accuracy = metric.get('directional_accuracy')
            window = f"{walk.get('holdout_start_period', 'Unknown')} to {walk.get('holdout_end_period', 'Unknown')}"
            metric_rows.append([name, outcome, window, method.replace('_', ' '), metric.get('n', walk.get('n_predictions', 'Unknown')),
                                fmt(metric.get('mae')), fmt(metric.get('rmse')),
                                fmt(accuracy * 100) + '%' if _number(accuracy) else 'Not available'])
    output += _table(['Indicator', 'Outcome', 'Test window', 'Method', 'Test observations', 'MAE (pp)', 'RMSE (pp)', 'Direction accuracy'], metric_rows)
    if not metric_rows:
        output += ['', 'No usable held-out model metrics were supplied; missing results are not zero errors.']
    if skipped:
        output += ['', 'Some comparisons do not support this quarterly prediction check:', ''] + _table(['Indicator', 'Outcome', 'Reason'], skipped)
    output += ['', '### How to use these results', '',
               'Inspect sample size, data span and the baseline comparison together. A large in-sample correlation can coexist with poor held-out errors. '
               'This report does not rank a universally best predictor, assign causal weights, or turn these retrospective checks into a future price forecast.', '']
    for caveat in research.get('caveats', []):
        output.append('- ' + str(caveat))
    research_files = run.get('research_files', {})
    if isinstance(research_files, dict):
        for name, path in research_files.items():
            if isinstance(path, str) and _safe_relative_path(path):
                output += ['', f"[{str(name).replace('_', ' ').title()}]({path})"]
    output += ['', '## Limitations and reproducibility', '',
               '- Reference dates, publication dates and retrieval dates have different meanings. Table updates do not establish historical observation-level availability.',
               '- Later revisions may affect all retrospective statistics. A strict historical-vintage validation requires archived releases and is not claimed here.',
               '- Each index and indicator retains its official coverage; private residential evidence is not automatically HDB evidence.',
               ('- Main-page values and comparisons are generated from saved calculations. Reasons labelled editorial_review are reviewed wording; other model-authored reasons remain qualitative judgements.'
                if review else '- Main-page values and comparisons are generated from saved calculations. Model-authored selection reasons below remain qualitative judgements and may contain errors.'),
               '- Replay verifies saved file hashes and regenerates this report without source or model calls. A source refresh creates a new run.']
    output += ['- ' + str(x) for x in run.get('warnings', [])]
    output += ['', '## Appendix: indicator selection', '',
               f"Evaluated {len(evaluations)} candidates; selected {len(chosen)}. Data quality measures usability, not predictive importance. "
               'A shared family can contain complementary measures; family diversity is a preference rather than evidence of optimal prediction.', '']
    if run.get('indicator_pool_files'):
        output += ['[Full indicator pool: definitions, selection reasons and official sources](indicator_pool.md) · [Searchable indicator table](indicator_pool.html)', '']
    decisions = {x['id']: x for x in selection.get('decisions', [])}
    output += _table(['Candidate', 'Family', 'Latest period', 'Quality', 'Decision', 'Reason origin', 'Reason'], [
        [x['metadata']['name'] + ' (' + x['id'] + ')', x['metadata'].get('selection_family', x['metadata'].get('theme', 'Unknown')),
         (x.get('latest') or {}).get('period', 'Unavailable'), _quality_label(x, enhanced),
         'Selected' if x['id'] in chosen_ids else 'Excluded', decisions.get(x['id'], {}).get('reason_origin', 'Not supplied'),
         decisions.get(x['id'], {}).get('reason', 'No decision reason supplied.')] for x in evaluations])
    output += ['', '## Appendix: definitions and calculation evidence', '']
    if enhanced:
        output += ['The economic response lags below are qualitative hypotheses. The statistical lag settings in the empirical checks '
                   'align observations; they do not establish an economic response delay or causation. '
                   'Update frequency describes the recorded release cadence, not an observation-level publication date.', '']
    for item in chosen:
        meta = item['metadata'];latest = item.get('latest') or {};provenance = meta.get('provenance', {})
        output += [f"### {meta['name']}", '', f"**Series:** `{item['id']}` · **Source:** {_source_link(item)}", '',
                   f"**Definition:** {meta.get('definition', 'Not supplied')}", '', f"**Coverage:** {meta.get('scope', 'See source')}", '',
                   f"**Frequency:** {_FREQUENCIES.get(meta.get('frequency'), meta.get('frequency', 'Unknown'))}; **Unit:** {meta.get('unit', 'Unknown')}; **Seasonal adjustment:** {meta.get('seasonal_adjustment', 'Not established')}", '',
                   f"**Observation reference date:** {latest.get('observation_date', 'Period end used conservatively')}; **Source table updated:** {meta.get('source_updated_at') or 'Not supplied'}; **Retrieved:** {meta.get('retrieved_at', 'Not supplied')}", '',
                   f"**Feature used for empirical checks:** {candidates.get(item['id'], {}).get('feature_definition', 'Not supplied or not estimable')}", '']
        if enhanced:
            output += [f"**Update frequency:** {meta.get('update_frequency') or 'Not supplied'}", '']
            output += _narrative_lines(run, item, selection)
        output += _table(['Evidence', 'Latest period', 'Base period', 'Formula', 'Latest input', 'Base input', 'Change'], [
            [x.get('id', ''), x.get('latest_period', ''), x.get('base_period', ''), x.get('formula', ''),
             fmt(x.get('latest_value')), fmt(x.get('base_value')), _change_text(x)] for x in item.get('changes', [])])
        if provenance.get('raw_file'):
            output += ['', f"Raw snapshot: `{provenance['raw_file']}`; SHA-256 `{provenance.get('raw_sha256', 'Not supplied')}`."]
        output += ['']
    return '\n'.join(output)


def render_report(run: dict, evaluations: list[dict], selection: dict, research: dict | None = None) -> str:
    if run.get('report_version') == 2:
        return _render_report_v2(run, evaluations, selection, research if research is not None else run.get('research', {}))
    return _render_report_v1(run, evaluations, selection)


def _safe_url(value):
    if not isinstance(value, str) or any(ord(char) < 32 for char in value):
        return None
    split = urlsplit(value)
    if split.scheme in ('http', 'https') and split.netloc and not split.username and not split.password:
        return value
    return _safe_relative_path(value)


def _image_url(value, asset_root):
    path = _safe_relative_path(value)
    if not path or Path(path).suffix.lower() not in ('.svg', '.png', '.jpg', '.jpeg', '.webp'):
        return None
    if asset_root is None:
        return path
    base = Path(asset_root).resolve()
    candidate = (base / path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    if not candidate.is_file() or candidate.stat().st_size > 5_000_000:
        return None
    mime = {'.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}[candidate.suffix.lower()]
    return 'data:' + mime + ';base64,' + base64.b64encode(candidate.read_bytes()).decode('ascii')


def _inline(text, asset_root=None):
    pattern = re.compile(r'(!?)\[([^\]\n]*)\]\(([^)\n]*)\)|\*\*([^*\n]+)\*\*|`([^`\n]+)`')
    result=[];position=0
    for match in pattern.finditer(text):
        result.append(html.escape(text[position:match.start()]))
        if match.group(4) is not None:
            result.append('<strong>' + html.escape(match.group(4)) + '</strong>')
        elif match.group(5) is not None:
            result.append('<code>' + html.escape(match.group(5)) + '</code>')
        else:
            image, label, target = match.group(1, 2, 3)
            url = _image_url(target, asset_root) if image else _safe_url(target)
            if url:
                escaped = html.escape(url, quote=True)
                result.append('<img loading="lazy" src="' + escaped + '" alt="' + html.escape(label, quote=True) + '">' if image else
                              '<a href="' + escaped + '">' + html.escape(label) + '</a>')
            else:
                result.append(html.escape(label) + (' [image unavailable]' if image else ''))
        position=match.end()
    result.append(html.escape(text[position:]))
    return ''.join(result)


def _render_html_v2(markdown, asset_root):
    lines = markdown.splitlines();body=[];index=0
    while index < len(lines):
        line=lines[index].strip()
        if not line or line == _V2_MARKER:
            index+=1;continue
        if line.startswith('|') and index+1 < len(lines) and re.fullmatch(r'[| :\-]+', lines[index+1].strip()):
            table=[]
            while index < len(lines) and lines[index].strip().startswith('|'):
                table.append([x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', lines[index].strip().strip('|'))]);index+=1
            body.append('<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">'+_inline(x,asset_root)+'</th>' for x in table[0])+'</tr></thead><tbody>')
            body.extend('<tr>'+''.join('<td>'+_inline(x,asset_root)+'</td>' for x in row)+'</tr>' for row in table[2:])
            body.append('</tbody></table></div>');continue
        heading=re.match(r'^(#{1,3})\s+(.*)$',line)
        if heading:
            level=len(heading[1]);label=heading[2];identifier=re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-')
            body.append(f'<h{level} id="{identifier}">'+_inline(label,asset_root)+f'</h{level}>');index+=1;continue
        if line.startswith('- '):
            body.append('<ul>')
            while index<len(lines) and lines[index].strip().startswith('- '):
                body.append('<li>'+_inline(lines[index].strip()[2:],asset_root)+'</li>');index+=1
            body.append('</ul>');continue
        paragraph=[_inline(line,asset_root) + ('<br>' if lines[index].endswith('  ') else '')];index+=1
        while index<len(lines) and lines[index].strip() and not re.match(r'^(#{1,3} |\||- )',lines[index].strip()):
            paragraph.append(_inline(lines[index].strip(),asset_root) + ('<br>' if lines[index].endswith('  ') else ''));index+=1
        body.append('<p>'+' '.join(paragraph)+'</p>')
    style='body{margin:0;background:#f4f6f9;color:#18283a;font:16px/1.65 system-ui,sans-serif}main{max-width:1180px;margin:32px auto;padding:36px;background:#fff;border-radius:14px}h1{font-size:2rem;line-height:1.2}h2{margin-top:2.5rem;padding-top:.8rem;border-top:2px solid #e5ebf2;color:#123f61}h3{margin-top:1.8rem}a{color:#086593}nav{display:flex;gap:18px;flex-wrap:wrap;border-bottom:1px solid #d9e3ed;padding-bottom:14px}p,li{max-width:1050px}.table-wrap{overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid #dce4ed}th{background:#edf3f8;white-space:nowrap}tr:nth-child(even){background:#f8fafc}td{min-width:90px}img{display:block;width:100%;height:auto;max-width:1100px;border:1px solid #e1e7ee;border-radius:8px}code{font-size:.84em;background:#edf1f5;padding:2px 4px;overflow-wrap:anywhere}strong{color:#163d5a}@media(max-width:700px){main{margin:0;padding:18px;border-radius:0}h1{font-size:1.6rem}}'
    nav='<nav aria-label="Report sections"><a href="#executive-summary">Summary</a><a href="#market-outcomes">Market outcomes</a><a href="#selected-signals">Selected signals</a><a href="#empirical-checks">Empirical checks</a><a href="#appendix-indicator-selection">Selection appendix</a></nav>'
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Singapore housing market research report</title><style>'+style+'</style></head><body><main>'+nav+''.join(body)+'</main></body></html>'


def render_html(markdown: str, asset_root: Path | str | None = None) -> str:
    if markdown.startswith(_V2_MARKER + '\n'):
        return _render_html_v2(markdown, asset_root)
    return _render_html_v1(markdown)
