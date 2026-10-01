"""Deterministic report rendering: numeric facts never come from free-form LLM text."""
from __future__ import annotations

import html
from pathlib import Path


def fmt(value) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, (int, float)):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_report(run: dict, evaluations: list[dict], selection: dict) -> str:
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


def render_html(markdown: str) -> str:
    # A dependency-free, searchable preview of the exact report; Markdown remains canonical.
    pool_link = ('<p><a href="indicator_pool.html">查看完整指标池表 · 定义、选择理由和官方来源</a></p>'
                 if "[可搜索的表格预览](indicator_pool.html)" in markdown else "")
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Housing research brief</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;background:#f6f7f9;color:#172033;font:16px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;border:1px solid #dbe1e8;padding:28px;border-radius:12px;font:inherit}</style><body>' + pool_link + '<pre>' + html.escape(markdown) + '</pre></body></html>'
