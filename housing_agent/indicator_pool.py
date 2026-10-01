"""Complete Chinese candidate-pool exports from saved, auditable run facts.

No network or model calls are made here. Editorial notes explain why a series is
a candidate; they never stand in for a model decision or a missing observation.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
from importlib.resources import files
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit


COLUMNS = ["指标", "口径与频率", "纳入候选池理由", "官方来源", "本次数据状态", "本次选择与理由", "限制"]
_FREQUENCIES = {"A": "年度", "Q": "季度", "M": "月度", "D": "日度"}
_UNITS = {"Per Cent": "%", "Per Cent Per Annum": "%/年", "Million Dollars": "百万新元", "Dollars": "新元", "Number Of Units": "套", "Index": "指数", "Number": "数量"}
_ORIGINS = {"model": "模型原始理由", "system": "系统补充说明（非模型理由）", "rules": "确定性筛选规则（非模型理由）", "unknown": "理由来源未标注", "missing": "未记录单项理由"}
_DISCLAIMERS = [
    "这是完整候选池，按配置顺序保留全部指标；进入候选池不等于进入本次报告。",
    "质量分只衡量数据可用性，未验证这些指标的预测能力，也不证明因果关系。",
    "中文候选理由与限制是随版本保存的编辑说明；模型或规则的本次选择理由另行标注，原文完整保留。",
    "没有原始文件来源或有效观测时，不填入旧数据，也不把失败记录中的占位零分当作真实质量评分。",
    "报告日期按观测参考日期或期间末筛选当前捕获版本，不等于重建当时可获得的信息集合。",
]


def _text(value, default="") -> str:
    return value if isinstance(value, str) and value.strip() else default


def _finite(value) -> bool:
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def _number(value) -> str:
    if not _finite(value):
        return "未提供"
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


def _list(value) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else ([str(value)] if value else [])


def _load_notes(notes):
    origin = "caller-supplied notes"
    if notes is None:
        origin = "housing_agent/data/indicator_notes.json"
        try:
            notes = json.loads(files("housing_agent").joinpath("data/indicator_notes.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            notes, origin = {}, "Chinese notes unavailable; source/configured definitions retained"
    if not isinstance(notes, dict) or any(not isinstance(key, str) or not isinstance(value, dict) for key, value in notes.items()):
        raise ValueError("Indicator notes must map series ids to note objects")
    serialized = json.dumps(notes, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return deepcopy(notes), origin, hashlib.sha256(serialized).hexdigest()


def _identifier(spec):
    if not isinstance(spec, dict) or not spec.get("table_id") or spec.get("row_id") is None:
        raise ValueError("Each candidate must have table_id and row_id")
    return f"{spec['table_id']}:{spec['row_id']}"


def _index(items, label):
    if not isinstance(items, list):
        raise ValueError(f"{label} must be a list")
    result = {}
    for item in items:
        if not isinstance(item, dict) or not _text(item.get("id")) or item["id"] in result:
            raise ValueError(f"{label} must contain distinct nonempty ids")
        result[item["id"]] = item
    return result


def _capture_range(rows):
    times = []
    missing = 0
    for row in rows:
        if not row["has_provenance"]:
            continue
        value = row["actual_metadata"].get("retrieved_at")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("No timezone")
            times.append((parsed.astimezone(timezone.utc), value))
        except (AttributeError, TypeError, ValueError):
            missing += 1
    times.sort(key=lambda pair: pair[0])
    return {"min": times[0][1] if times else None, "max": times[-1][1] if times else None,
            "captured_series_with_timestamp": len(times), "captured_series_missing_timestamp": missing}


def _rule_reason_zh(reason, status):
    """Translate only known rule templates; never invent or translate model prose."""
    if not isinstance(reason, str):
        return ""
    if status == "selected" and re.fullmatch(
        r"Selected for economic-family coverage \(.+\): highest data-quality score within this family, with deterministic id tie-breaking\. The family defaults to the theme when not specified\.", reason
    ):
        return "在该经济类别中数据质量分最高，优先补足类别覆盖；同分按指标 ID 排序。"
    if status == "selected" and re.fullmatch(
        r"Selected to fill remaining capacity by data-quality score after economic-family coverage; family: .+\.", reason
    ):
        return "先覆盖不同经济类别，再按数据质量分补足剩余名额。"
    if status == "eligible_unselected" and re.fullmatch(
        r"Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: .+\.", reason
    ):
        return "按经济类别覆盖、数据质量分及同分时的指标 ID 顺序选择后，报告名额已满。"
    return ""


def build_indicator_pool(run: dict, catalogue: list[dict], evaluations: list[dict], selection: dict,
                         *, notes: dict | None = None) -> dict:
    """Join every configured candidate to actual run facts and exact decisions.

    Optional notes make offline tests and version-pinned export straightforward.
    The used notes are embedded and canonically hashed in the returned artifact.
    """
    if not isinstance(run, dict) or not isinstance(selection, dict) or not isinstance(catalogue, list):
        raise ValueError("run/selection must be objects and catalogue must be a list")
    note_data, note_origin, note_hash = _load_notes(notes)
    evaluated = _index(evaluations, "evaluations")
    decisions = _index(selection.get("decisions", []), "decisions")
    selected_list = selection.get("selected_ids", [])
    if not isinstance(selected_list, list) or any(not isinstance(key, str) for key in selected_list):
        raise ValueError("selected_ids must be a list of strings")
    selected_ids = set(selected_list)
    selection_completed = "selected_ids" in selection
    rows, ids = [], set()
    warnings = []
    for spec in catalogue:
        identifier = _identifier(spec)
        if identifier in ids:
            raise ValueError("The candidate catalogue contains duplicate ids")
        ids.add(identifier)
        note = note_data.get(identifier, {})
        evaluation = evaluated.get(identifier, {})
        actual = evaluation.get("metadata", {})
        actual = actual if isinstance(actual, dict) else {}
        provenance = actual.get("provenance", {})
        has_source = isinstance(provenance, dict) and bool(_text(provenance.get("raw_file")) and _text(provenance.get("raw_sha256")))
        supplied_latest = evaluation.get("latest")
        has_latest = has_source and isinstance(supplied_latest, dict) and bool(_text(supplied_latest.get("period"))) and _finite(supplied_latest.get("value"))
        latest = deepcopy(supplied_latest) if has_latest else None
        original_quality = evaluation.get("quality", {})
        original_quality = original_quality if isinstance(original_quality, dict) else {}
        assessed = has_latest and isinstance(original_quality.get("eligible"), bool)
        quality = deepcopy(original_quality) if assessed else {
            "eligible": None, "score": None, "reasons": _list(original_quality.get("reasons")),
            "warnings": _list(original_quality.get("warnings")), "assessment_status": "not_assessed_without_provenance_or_latest",
        }
        score = quality.get("score")
        if not _finite(score) or not 0 <= score <= 100:
            quality["score"] = None
        reasons = _list(original_quality.get("reasons"))
        decision = decisions.get(identifier)
        exact_reason = decision.get("reason") if decision is not None else None
        origin = decision.get("reason_origin") if decision is not None else "missing"
        if origin not in _ORIGINS:
            origin = "rules" if run.get("mode") == "rules" and decision is not None else "unknown"
        requested_selected = identifier in selected_ids
        if not has_source:
            maintenance = bool(re.search(r"maintenance|维护", " ".join(reasons + ([exact_reason] if isinstance(exact_reason, str) else [])), re.I))
            status = "maintenance_unavailable" if maintenance else "unavailable"
            status_label = "维护期间未获取" if maintenance else "本次未获取"
            summary = status_label + "；未进行本次质量评分，不能据此认定指标无效。"
            group = "unavailable"
        elif not has_latest:
            status, status_label, group = "no_usable_observation", "已获取，无可用观测", "ineligible"
            summary = "已有源文件，但报告截止日前没有有效观测；不显示质量分数。"
        elif not assessed:
            status, status_label, group = "unassessed", "已获取，尚未评估", "pending"
            summary = "已有观测，但缺少本次质量评估记录。"
        elif quality["eligible"] is False:
            status, status_label, group = "ineligible", "未通过数据门槛", "ineligible"
            summary = "已有观测，但未通过本次数据质量门槛；这不是预测能力评判。"
        elif requested_selected:
            status, status_label, group = "selected", "已选入本次报告", "selected"
            summary = "已选；满足本次数据门槛。"
        elif selection_completed:
            status, status_label, group = "eligible_unselected", "数据合格，本次落选", "eligible_unselected"
            summary = "已达到数据门槛，未进入本次报告；不代表预测能力较差。"
        else:
            status, status_label, group = "eligible_pending", "数据合格，尚未选择", "pending"
            summary = "已达到数据门槛，但本次尚无选择结果。"
        if requested_selected and status != "selected":
            warnings.append(f"{identifier} 的选择记录与数据状态不一致；未把它显示为有效入选。")
            summary += "选择记录与数据状态不一致，需核查原始记录。"
        if origin == "system":
            summary += "原因为系统补充，不能当作模型逐项解释。"
        elif origin == "model":
            summary += "模型选择理由见原文。"
        elif origin == "rules":
            summary += _rule_reason_zh(exact_reason, status) + "由确定性规则选择，未调用模型解释。"
        else:
            summary += _ORIGINS[origin] + "。"

        configured_definition = _text(spec.get("definition"), "配置未提供口径")
        actual_definition = _text(actual.get("definition")) if has_source else ""
        definition = actual_definition or configured_definition
        if actual_definition and actual_definition != configured_definition:
            definition_zh = "本次实际来源口径：" + actual_definition
        else:
            definition_zh = _text(note.get("definition_zh"), definition)
        name = _text(actual.get("name"), _text(spec.get("expected_name"), identifier))
        frequency = actual.get("frequency", spec.get("frequency")) if has_source else spec.get("frequency")
        unit = actual.get("unit", spec.get("expected_unit")) if has_source else spec.get("expected_unit")
        unit_zh = "人" if unit == "Number" and str(spec.get("table_id")) == "M810001" else _UNITS.get(unit, str(unit or "未注明"))
        planned_url = _text(note.get("planned_source_url"), f"https://tablebuilder.singstat.gov.sg/table/TS/{spec['table_id']}")
        source = {
            "kind": "actual" if has_source else "configured_only",
            "url": _text(actual.get("source_url"), planned_url) if has_source else planned_url,
            "label": _text(actual.get("source_provider"), "SingStat Table Builder") if has_source else _text(note.get("planned_source_label"), "SingStat Table Builder"),
            "agency": _text(actual.get("source_agency"), _text(note.get("source_agency"), "机构未注明")) if has_source else _text(note.get("source_agency"), "机构未注明"),
            "status_label": "本次实际来源" if has_source else "配置来源，本次未获取",
            "planned_url": planned_url, "planned_label": _text(note.get("planned_source_label"), "SingStat Table Builder"),
        }
        data_status = status_label
        if latest:
            data_status = f"最新可用：{latest['period']}；{_number(latest['value'])} {unit_zh}"
            if latest.get("preliminary"):
                data_status += "；初步值（官方标记）"
        else:
            data_status += "；最新期间和值：未提供"
        data_status += f"；质量分：{_number(quality.get('score'))}/100" if quality.get("score") is not None else "；质量分：未评估或未提供"
        rows.append({
            "id": identifier, "name_zh": _text(note.get("name_zh"), name), "name": name,
            "definition": definition, "definition_zh": definition_zh,
            "definition_origin": "actual_metadata" if actual_definition else "catalogue",
            "frequency": frequency, "frequency_zh": _FREQUENCIES.get(frequency, str(frequency or "未注明")),
            "unit": unit, "unit_zh": unit_zh, "scope": actual.get("scope", spec.get("scope")) if has_source else spec.get("scope"),
            "rationale_zh": _text(note.get("rationale_zh"), "候选池理由的中文说明尚未提供；请核对配置中的经济机制。"),
            "caveat_zh": _text(note.get("caveat_zh"), "应结合定义、覆盖范围、数据质量及经济机制审阅；不构成预测验证。"),
            "source": source, "has_provenance": has_source, "has_latest": has_latest,
            "latest": latest, "quality_assessed": assessed, "quality": quality,
            "data_status_zh": data_status, "status": status, "status_label": status_label, "filter_group": group,
            "selected": status == "selected", "selection_record_selected": requested_selected,
            "selection_summary_zh": summary, "decision_reason": exact_reason,
            "decision_reason_origin": origin, "decision_origin_label": _ORIGINS[origin],
            "original_decision": deepcopy(decision), "actual_metadata": deepcopy(actual),
            "catalogue_entry": deepcopy(spec), "evaluation_reference": "evaluations.json#" + identifier,
            "changes": deepcopy(evaluation.get("changes", [])) if has_latest else [],
        })
    unknown = (set(evaluated) | set(decisions) | selected_ids) - ids
    if unknown:
        warnings.append("运行记录含不在本候选目录中的 ID，未加入目录：" + ", ".join(sorted(unknown)))
    saved = isinstance(run.get("source_run"), dict) or run.get("source_policy") == "saved"
    source_run = run.get("source_run") if isinstance(run.get("source_run"), dict) else {}
    return {
        "schema_version": 1, "title": "新加坡住宅市场：完整候选指标池", "columns": COLUMNS.copy(),
        "run": {key: deepcopy(run.get(key)) for key in ("run_id", "as_of", "created_at", "mode", "mode_label", "status", "source_policy", "data_basis", "source_run")},
        "source_run_id": source_run.get("name") or run.get("run_id"),
        "snapshot_reused": saved,
        "source_capture": _capture_range(rows),
        "source_capture_note": "复用已保存的来源快照；沿用原抓取时间，本次没有重新取数。" if saved else "实际来源的抓取时间见下；抓取时间不等于数据观测期或官方发布日期。",
        "selection_method": selection.get("method"), "rows": rows,
        "counts": {"candidates": len(rows), "selected": sum(row["selected"] for row in rows), "by_status": dict(Counter(row["status"] for row in rows))},
        "notes": note_data, "notes_origin": note_origin, "notes_sha256": note_hash,
        "notes_hash_policy": "SHA-256 of UTF-8 JSON with sorted keys, ensure_ascii=False and compact separators",
        "disclaimers": _DISCLAIMERS.copy(), "warnings": warnings,
    }


def _safe_url(value):
    if not isinstance(value, str) or re.search(r"[\s\x00-\x1f\x7f\\]", value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return None
        _ = parsed.port
    except ValueError:
        return None
    return value


def _escape(value):
    return html.escape(str(value if value is not None else "未提供"), quote=True)


def _md(value):
    escaped = _escape(value).replace("\\", "\\\\")
    for character in "|`*_[]()#!":
        escaped = escaped.replace(character, "\\" + character)
    return escaped.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def _header_lines(pool):
    run, capture = pool["run"], pool["source_capture"]
    export = pool.get("export_provenance")
    exported = (["依据已保存运行导出；未刷新数据、未重新筛选、未调用模型。",
                 "本表导出时间：" + str(export.get("exported_at") or "未提供")]
                if isinstance(export, dict) else [])
    return exported + [
        f"报告截止日期：{run.get('as_of') or '未提供'}；运行：{run.get('run_id') or '未提供'}；来源运行：{pool.get('source_run_id') or '未提供'}",
        f"原运行报告生成时间：{run.get('created_at') or '未提供'}；模式：{run.get('mode_label') or run.get('mode') or '未注明'}",
        pool["source_capture_note"],
        f"实际来源抓取范围：{capture.get('min') or '未提供'} 至 {capture.get('max') or '未提供'}；{capture['captured_series_missing_timestamp']} 项已获取来源缺少有效时区时间戳。",
        f"共 {pool['counts']['candidates']} 个候选，{pool['counts']['selected']} 个进入本次报告。",
    ]


def _details(row):
    actual = row["actual_metadata"]
    fields = [
        ("选择理由来源", row["decision_origin_label"]), ("选择理由原文", row["decision_reason"] if row["decision_reason"] is not None else "未记录"),
        ("来源定义原文", row["definition"]), ("来源覆盖范围", row.get("scope")),
        ("数据门槛原因原文", "\n".join(_list(row["quality"].get("reasons"))) or "未提供"),
        ("数据警告原文", "\n".join(_list(row["quality"].get("warnings"))) or "未提供"),
    ]
    for key, label in (("source_footnote", "源文件注释"), ("row_footnote", "源行注释"), ("transformation_note", "来源转换说明")):
        if actual.get(key):
            fields.append((label, actual[key]))
    if row["has_provenance"]:
        provenance = actual["provenance"]
        fields.extend([("原始文件", provenance.get("raw_file")), ("原始文件 SHA-256", provenance.get("raw_sha256"))])
    return fields


def _source_markdown(source):
    url = _safe_url(source["url"])
    link = f"[{_md(source['label'])}](<{html.escape(url, quote=True)}>)" if url else _md(source["label"]) + "（链接格式未通过检查）"
    return _md(source["agency"]) + "<br>" + link + "<br>" + _md(source["status_label"])


def _render_markdown(pool):
    output = ["# " + _md(pool["title"]), ""]
    output += [_md(line) + "<br>" for line in _header_lines(pool)]
    output += ["", *["> " + _md(text) for text in pool["disclaimers"]], "",
               "| " + " | ".join(pool["columns"]) + " |", "|" + "---|" * len(pool["columns"])]
    for row in pool["rows"]:
        values = [
            _md(row["name_zh"]) + "<br>" + _md(row["id"]),
            _md(row["definition_zh"]) + "<br>" + _md(row["frequency_zh"] + "；" + row["unit_zh"]),
            _md(row["rationale_zh"]), _source_markdown(row["source"]), _md(row["data_status_zh"]),
            _md(row["selection_summary_zh"]) + "<br>" + _md(row["decision_origin_label"] + "；原文见下方折叠依据"),
            _md(row["caveat_zh"]),
        ]
        output.append("| " + " | ".join(values) + " |")
    output += ["", "## 原始依据", ""]
    for row in pool["rows"]:
        output += [f"<details><summary>{_escape(row['name_zh'])}（{_escape(row['id'])}）</summary>", ""]
        for label, value in _details(row):
            output += [f"<p><strong>{_escape(label)}</strong></p><pre>{_escape(value)}</pre>", ""]
        output += ["</details>", ""]
    if pool["warnings"]:
        output += ["## 导出检查", "", *["- " + _md(warning) for warning in pool["warnings"]], ""]
    output += ["中文说明来源：" + _md(pool["notes_origin"]), "", "说明内容 SHA-256：`" + pool["notes_sha256"] + "`。完整说明随 JSON 保存。", ""]
    return "\n".join(output)


def _render_html(pool):
    rows = []
    for row in pool["rows"]:
        source = row["source"]
        url = _safe_url(source["url"])
        source_link = (f'<a href="{_escape(url)}" target="_blank" rel="noopener noreferrer">{_escape(source["label"])}</a>'
                       if url else _escape(source["label"]) + "（链接格式未通过检查）")
        details = '<details><summary>查看原始决定与来源依据</summary>' + "".join(
            f'<p><strong>{_escape(label)}</strong></p><pre>{_escape(value)}</pre>' for label, value in _details(row)
        ) + "</details>"
        cells = [
            f'<strong>{_escape(row["name_zh"])}</strong><small>{_escape(row["id"])}</small>',
            f'{_escape(row["definition_zh"])}<small>{_escape(row["frequency_zh"])} · {_escape(row["unit_zh"])}</small>',
            _escape(row["rationale_zh"]),
            f'{_escape(source["agency"])}<br>{source_link}<small>{_escape(source["status_label"])}</small>',
            f'<span class="badge {row["filter_group"]}">{_escape(row["status_label"])}</span><p>{_escape(row["data_status_zh"])}</p>',
            f'{_escape(row["selection_summary_zh"])}<small>{_escape(row["decision_origin_label"])}</small>{details}',
            _escape(row["caveat_zh"]),
        ]
        rows.append(f'<tr data-filter="{_escape(row["filter_group"])}">' + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    header = "".join(f"<p>{_escape(line)}</p>" for line in _header_lines(pool))
    caveats = "".join(f"<li>{_escape(item)}</li>" for item in pool["disclaimers"] + pool["warnings"])
    overview = f"报告截止日期：{pool['run'].get('as_of') or '未提供'} · {pool['counts']['candidates']} 个候选 · {pool['counts']['selected']} 个入选"
    notice = ("依据已保存运行导出；未刷新数据、未重新筛选、未调用模型。"
              if isinstance(pool.get("export_provenance"), dict) else pool["source_capture_note"])
    return '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>新加坡住宅市场：完整候选指标池</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#172c3a;font:15px/1.65 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1900px;margin:auto;padding:30px 24px}h1{font-size:28px;margin:0 0 16px}header p{margin:5px 0;color:#4a5c69}aside{background:#eaf1f6;border-left:4px solid #34749b;padding:12px 18px;margin:22px 0}aside ul{margin:0;padding-left:20px}.controls{display:flex;align-items:end;gap:16px;flex-wrap:wrap;margin:20px 0}label{font-weight:600}input,select{display:block;margin-top:5px;border:1px solid #bccbd6;border-radius:7px;background:white;color:inherit;padding:10px 12px;font:inherit}input{min-width:300px}#count{color:#5a6c78;padding-bottom:11px}.table-wrap{overflow:auto;border:1px solid #d0dbe4;border-radius:10px;background:white;max-height:78vh}table{border-collapse:separate;border-spacing:0;table-layout:fixed;min-width:1300px;width:100%}th,td{padding:16px;text-align:left;vertical-align:top;border-right:1px solid #e4eaf0;border-bottom:1px solid #e4eaf0;overflow-wrap:anywhere}th{position:sticky;top:0;background:#e9f0f5;color:#233e52;z-index:2;font-weight:650}th:first-child,td:first-child{position:sticky;left:0;z-index:1;background:#f8fbfd}th:first-child{z-index:3}th:nth-child(1){width:12%}th:nth-child(2){width:16%}th:nth-child(3){width:14%}th:nth-child(4){width:12%}th:nth-child(5){width:16%}th:nth-child(6){width:16%}th:nth-child(7){width:14%}tbody tr:hover td{background:#f3f8fc}small{display:block;color:#667b8c;font-size:12px;margin-top:9px}td p{margin:10px 0 0}.badge{display:inline-block;padding:3px 8px;border-radius:5px;background:#edf1f4;font-size:12px;font-weight:600}.selected{background:#e0f2e7;color:#1f6440}.unavailable{background:#fff0d8;color:#805018}.ineligible{background:#f8e8e6;color:#873d37}.eligible_unselected{background:#e4edf8;color:#305984}a{color:#165d91;text-underline-offset:3px}details{margin-top:14px;border-top:1px solid #dde5eb;padding-top:9px}summary{cursor:pointer;color:#215777;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace;background:#f2f5f8;padding:9px;border-radius:4px}details p{font-size:12px;margin:10px 0 5px}.run-details{margin-top:12px}.run-details>summary{font-size:14px}.run-details>p{font-size:13px}footer{color:#637787;font-size:12px;overflow-wrap:anywhere;margin-top:20px}[hidden]{display:none!important}@media(max-width:650px){main{padding:20px 12px}h1{font-size:23px}input{min-width:0;width:100%}.controls label:first-child{width:100%}.table-wrap{max-height:74vh}th,td{padding:12px}}
</style></head><body><main>''' + f'<header><h1>{_escape(pool["title"])}</h1><p><strong>{_escape(overview)}</strong></p><p>{_escape(notice)}</p></header><details class="run-details"><summary>查看运行时间、来源范围与阅读说明</summary>{header}<aside><ul>{caveats}</ul></aside></details>' + '''
<div class="controls"><label>搜索指标、来源、口径或理由<input id="search" type="search" placeholder="例如：SORA、维护、收入" autocomplete="off"></label>
<label>筛选本次状态<select id="status"><option value="all">全部候选</option value="selected">已选入报告</option><option value="eligible_unselected">合格但未选</option><option value="ineligible">不合格或无有效观测</option><option value="unavailable">本次未获取（含维护）</option><option value="pending">待评估或待选择</option></select></label><span id="count" role="status" aria-live="polite"></span></div>
<div class="table-wrap" tabindex="0" aria-label="完整候选指标池，可横向滚动"><table><thead><tr>''' + "".join(f"<th scope=\"col\">{_escape(column)}</th>" for column in pool["columns"]) + "</tr></thead><tbody>" + "".join(rows) + '</tbody></table></div><footer>' + _escape("中文说明来源：" + pool["notes_origin"] + "；内容 SHA-256：" + pool["notes_sha256"] + "。完整说明与原始决定保存在配套 JSON 中。") + '''</footer></main>
<script>
const search=document.getElementById('search'),status=document.getElementById('status'),count=document.getElementById('count');
const rows=Array.from(document.querySelectorAll('tbody tr'));
function filterRows(){const term=search.value.trim().toLocaleLowerCase(),state=status.value;let visible=0;for(const row of rows){const matches=(state==='all'||row.dataset.filter===state)&&row.textContent.toLocaleLowerCase().includes(term);row.hidden=!matches;if(matches)visible++;}count.textContent=visible+' / '+rows.length+' 项候选';}
search.addEventListener('input',filterRows);status.addEventListener('change',filterRows);filterRows();
</script></body></html>'''


def write_indicator_pool(output: Path, pool: dict) -> None:
    """Save three standalone representations; render HTML as an actual table."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(pool, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    markdown, page = _render_markdown(pool), _render_html(pool)
    (output / "indicator_pool.json").write_text(serialized, encoding="utf-8")
    (output / "indicator_pool.md").write_text(markdown, encoding="utf-8")
    (output / "indicator_pool.html").write_text(page, encoding="utf-8")
