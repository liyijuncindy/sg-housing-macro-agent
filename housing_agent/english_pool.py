"""English-only presentation of captured candidate facts and exact decisions."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import html
import json
import math
from pathlib import Path
from urllib.parse import urlsplit


COLUMNS = ["Candidate", "Definition and frequency", "Candidate rationale", "Official source",
           "Data status", "Selection and reason", "Limitations"]


def number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return "Not available"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def build_english_pool(run, catalogue, evaluations, selection):
    evaluated = {item["id"]: item for item in evaluations}
    decisions = {item["id"]: item for item in selection.get("decisions", [])}
    selected = set(selection.get("selected_ids", []))
    rows = []
    for spec in catalogue:
        key = f"{spec['table_id']}:{spec['row_id']}"
        item = evaluated.get(key, {})
        actual = item.get("metadata", {})
        provenance = actual.get("provenance", {})
        captured = bool(provenance.get("raw_file") and provenance.get("raw_sha256"))
        latest = item.get("latest") if captured else None
        assessed = latest is not None and isinstance(item.get("quality", {}).get("eligible"), bool)
        quality = deepcopy(item.get("quality", {}))
        if not assessed:
            quality.update(eligible=None, score=None)
        meta = actual if captured else spec
        decision = decisions.get(key, {})
        status = ("unavailable" if not captured else "ineligible" if not assessed or not quality["eligible"]
                  else "selected" if key in selected else "eligible_unselected")
        mechanism = spec.get("mechanism", {})
        source = {"agency": meta.get("source_agency", "See official table"),
                  "label": meta.get("source_provider", "SingStat Table Builder"),
                  "url": meta.get("source_url", f"https://tablebuilder.singstat.gov.sg/table/TS/{spec['table_id']}"),
                  "kind": "captured" if captured else "configured; not captured in this run"}
        rows.append({"id": key, "name": meta.get("name", spec["expected_name"]),
                     "definition": meta.get("definition", spec.get("definition", "Not supplied")),
                     "scope": meta.get("scope", spec.get("scope", "Not supplied")),
                     "frequency": meta.get("frequency", spec["frequency"]),
                     "unit": meta.get("unit", spec["expected_unit"]),
                     "selection_family": spec.get("selection_family", spec.get("theme")),
                     "candidate_rationale": "Sales: " + mechanism.get("sales", "Not supplied") +
                                            " Rent: " + mechanism.get("rents", "Not supplied"),
                     "limitations": mechanism.get("limitations", "See source scope and data quality."),
                     "source": source, "status": status, "selected": status == "selected",
                     "quality": quality, "latest": deepcopy(latest),
                     "changes": deepcopy(item.get("changes", [])) if latest else [],
                     "decision_reason": decision.get("reason", "No individual reason recorded."),
                     "decision_reason_origin": decision.get("reason_origin", "rules" if run.get("mode") == "rules" else "missing"),
                     "provenance": deepcopy(provenance) if captured else None,
                     "retrieved_at": actual.get("retrieved_at") if captured else None})
    return {"schema_version": 2, "language": "en", "title": "Singapore housing: full candidate indicator pool",
            "columns": COLUMNS, "run": {key: deepcopy(run.get(key)) for key in
            ("run_id", "as_of", "created_at", "mode", "mode_label", "source_policy", "source_run", "data_basis")},
            "rows": rows, "counts": {"candidates": len(rows), "selected": sum(r["selected"] for r in rows),
            "by_status": dict(Counter(r["status"] for r in rows))},
            "disclaimers": ["Candidate inclusion is an editorial research hypothesis; each run's selection reason is recorded separately.",
                             "Quality scores describe source-data usability, not forecast accuracy or causation.",
                             "Configured sources without captured files are not evidence of successful retrieval.",
                             "Annual, quarterly and monthly observations retain their actual periods; no interpolation is performed.",
                             "Historical analysis uses the latest captured vintage, not a reconstructed publication-time information set."]}


def _escape(value):
    return html.escape(str(value if value is not None else "Not available"), quote=True)


def _url(value):
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password else None
    except (ValueError, TypeError):
        return None


def _values(row):
    latest = row["latest"]
    quality = row["quality"]
    status = (f"{latest['period']}: {number(latest['value'])} {row['unit']}; quality {number(quality.get('score'))}/100"
              if latest and quality.get("score") is not None else "No assessed usable observation")
    return [f"{row['name']} ({row['id']})", f"{row['definition']} Frequency: {row['frequency']}; unit: {row['unit']}.",
            row["candidate_rationale"], f"{row['source']['agency']} via {row['source']['label']} ({row['source']['kind']})",
            status, f"{row['status']}; reason origin: {row['decision_reason_origin']}. {row['decision_reason']}", row["limitations"]]


def write_english_pool(output: Path, pool: dict):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    run = pool["run"]
    intro = f"Observation cutoff: {run['as_of']}. Run: {run['run_id']}. {pool['counts']['candidates']} candidates; {pool['counts']['selected']} selected."
    markdown = ["# " + pool["title"], "", intro, "", str(run.get("data_basis", "")), "",
                *["> " + text for text in pool["disclaimers"]], "", "| " + " | ".join(COLUMNS) + " |",
                "|" + "---|" * len(COLUMNS)]
    html_rows = []
    for row in pool["rows"]:
        values = _values(row)
        markdown.append("| " + " | ".join(_escape(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |")
        cells = [_escape(v) for v in values]
        url = _url(row["source"]["url"])
        if url:
            cells[3] += f'<br><a href="{_escape(url)}" target="_blank" rel="noopener">Official source</a>'
        cells[5] += '<details><summary>Source evidence</summary><pre>' + _escape(json.dumps({"scope":row["scope"],"quality":row["quality"],"provenance":row["provenance"]},ensure_ascii=False,indent=2)) + '</pre></details>'
        html_rows.append(f'<tr data-status="{_escape(row["status"])}">' + "".join("<td>"+c+"</td>" for c in cells) + "</tr>")
    markdown += ["", "## Evidence and source links", ""]
    for row in pool["rows"]:
        url = _url(row["source"]["url"])
        markdown += [f"- {row['id']}: " + (f"[Official source]({url})" if url else "Source link unavailable") +
                     "; captured at " + str(row["retrieved_at"] or "not captured") + "."]
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Housing indicator pool</title><style>
body{margin:32px;background:#f5f7fb;color:#172c3a;font:15px/1.6 system-ui}h1{font-size:28px}aside{background:#eaf1f7;padding:12px 20px}.controls{display:flex;gap:16px;margin:24px 0;flex-wrap:wrap}input,select{padding:9px;font:inherit}.table-wrap{overflow:auto;max-height:75vh;background:white;border:1px solid #ccd9e5}table{border-collapse:collapse;min-width:1600px}th,td{padding:14px;vertical-align:top;border:1px solid #dce4ec;min-width:190px;max-width:330px}th{position:sticky;top:0;background:#e9f0f6;text-align:left}a{color:#176798}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.5 monospace}details{margin-top:12px}summary{cursor:pointer}[hidden]{display:none}
</style></head><body>''' + f'<h1>{_escape(pool["title"])}</h1><p>{_escape(intro)}</p><p>{_escape(run.get("data_basis"))}</p><aside>' + "".join("<p>"+_escape(d)+"</p>" for d in pool["disclaimers"]) + '''</aside><div class="controls"><label>Search candidates, sources and reasons <input id="search" type="search"></label><label>Status <select id="status"><option value="all">All candidates</option><option value="selected">Selected</option><option value="eligible_unselected">Eligible, not selected</option><option value="ineligible">Ineligible</option><option value="unavailable">Unavailable</option></select></label><span id="count" role="status"></span></div><div class="table-wrap"><table><thead><tr>''' + "".join("<th>"+_escape(c)+"</th>" for c in COLUMNS) + "</tr></thead><tbody>" + "".join(html_rows) + '''</tbody></table></div><script>
const search=document.getElementById('search'),status=document.getElementById('status'),count=document.getElementById('count'),rows=[...document.querySelectorAll('tbody tr')];
function filter(){let n=0;for(const r of rows){const ok=(status.value==='all'||r.dataset.status===status.value)&&r.textContent.toLowerCase().includes(search.value.trim().toLowerCase());r.hidden=!ok;if(ok)n++;}count.textContent=n+' / '+rows.length+' candidates';}search.addEventListener('input',filter);status.addEventListener('change',filter);filter();
</script></body></html>'''
    (output/"indicator_pool.json").write_text(json.dumps(pool,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    (output/"indicator_pool.md").write_text("\n".join(markdown)+"\n",encoding="utf-8")
    (output/"indicator_pool.html").write_text(page,encoding="utf-8")
