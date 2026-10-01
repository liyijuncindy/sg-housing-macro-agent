"""Independently check a captured SingStat v2 run; never edit its artifacts."""
from __future__ import annotations

import argparse
import calendar
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from housing_agent.storage import verify_inventory


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ordinal(period, frequency):
    year = int(period[:4])
    return year if frequency == "A" else year * 4 + int(period[-1]) - 1 if frequency == "Q" else year * 12 + int(period[-2:]) - 1


def raw_period(period, frequency):
    if frequency == "A":
        return str(int(period))
    if frequency == "Q":
        year, quarter = re.fullmatch(r"(\d{4}) ([1-4])Q", period).groups()
        return f"{year}-Q{quarter}"
    year, month = period.split()
    return f"{year}-{list(calendar.month_abbr).index(month):02}"


def changes(values, offset, kind):
    result = {}
    for period, current in values.items():
        base = values.get(period - offset)
        if base is None or kind == "percent" and base == 0:
            continue
        result[period] = float((current / base - 1) * 100 if kind == "percent" else
                               (current - base) * (100 if kind == "basis_point" else 1))
    return result


def audit(root):
    manifest = read(root / "manifest.json")
    assert manifest["status"] == "complete"
    verify_inventory(root, manifest)
    candidates = read(root / "evaluations.json")
    outcomes = read(root / "outcomes_evaluations.json")
    research = read(root / "research.json")
    count = 0
    for series in read(root / "normalized.json") + read(root / "outcomes_normalized.json"):
        provenance = series["provenance"]
        data = read(root / provenance["raw_file"])["Data"]
        row = next(r for r in data["row"] if str(r["seriesNo"]) == str(series["row_id"]))
        for obs in series["observations"]:
            cell = row["columns"][obs["raw_index"]]
            assert obs["raw_period"] == cell["key"] and obs["raw_value"] == cell["value"]
            assert obs["period"] == raw_period(cell["key"], series["frequency"])
            if obs["value"] is not None:
                assert float(Decimal(cell["value"].replace(",", ""))) == obs["value"]
            count += 1
    formula_differences = []
    for item in candidates + outcomes:
        kind = item["metadata"]["change_kind"]
        for change in item["changes"]:
            if change["value"] is None:
                continue
            current, base = Decimal(str(change["latest_value"])), Decimal(str(change["base_value"]))
            value = (current / base - 1) * 100 if kind == "percent" else (current - base) * (100 if kind == "basis_point" else 1)
            difference = abs(value - Decimal(str(change["value"])))
            assert difference < Decimal("1e-8")
            formula_differences.append(float(difference))
    features, targets = {}, {}
    for item in candidates:
        frequency = item["metadata"]["frequency"]
        values = {ordinal(o["period"], frequency): Decimal(str(o["value"])) for o in item["observations"]
                  if o["value"] is not None and int(o["period"][:4]) >= 2015}
        transformed = changes(values, {"A":1, "Q":4, "M":12}[frequency], item["metadata"]["change_kind"])
        if frequency == "M":
            transformed = {(k // 12) * 4 + (k % 12) // 3: v for k,v in transformed.items() if (k % 12 + 1) % 3 == 0}
        features[item["id"]] = transformed
    for item in outcomes:
        values = {ordinal(o["period"], "Q"): Decimal(str(o["value"])) for o in item["observations"]
                  if o["value"] is not None and int(o["period"][:4]) >= 2015}
        targets[item["id"]] = (changes(values, 1, "percent"),
                              {k//4:v for k,v in changes(values, 4, "percent").items() if k%4 == 3})
    correlations, predictions, metrics = 0, 0, 0
    corr_diffs, prediction_diffs, metric_diffs = [], [], []
    for comparison in research["comparisons"]:
        f = features[comparison["candidate_id"]]
        t = targets[comparison["outcome_id"]][comparison["analysis_frequency"] == "annual"]
        for row in comparison["correlations"]:
            pairs = [(v,t[k+row["lag"]]) for k,v in f.items() if k+row["lag"] in t]
            assert len(pairs) == row["n"]
            if row["pearson_r"] is not None:
                actual = np.corrcoef(np.array(pairs).T)[0,1]
                diff = abs(float(actual) - row["pearson_r"]);assert diff < 1e-8
                corr_diffs.append(diff);correlations += 1
        walk = comparison["walk_forward"]
        if walk["status"] != "evaluated":
            continue
        pairs = [(k,v,t[k+1],t[k]) for k,v in sorted(f.items()) if k in t and k+1 in t]
        calculated = []
        for index in range(24, len(pairs)):
            origin,feature,actual,last = pairs[index]
            train = np.array([(p[1],p[2]) for p in pairs[:index]])
            mean,scale = train[:,0].mean(),train[:,0].std()
            if scale <= 1e-12:
                predicted = train[:,1].mean()
            else:
                design = np.column_stack([np.ones(index),(train[:,0]-mean)/scale])
                coefficient = np.linalg.solve(design.T @ design + np.diag([0.,1.]), design.T @ train[:,1])
                predicted = coefficient @ np.array([1.,(feature-mean)/scale])
            stored = walk["predictions"][index-24]
            assert ordinal(stored["origin_period"],"Q") == origin
            assert ordinal(stored["target_period"],"Q") == origin+1
            assert ordinal(stored["training_target_end"],"Q") <= origin
            diff = abs(float(predicted)-stored["ridge"]);assert diff < 1e-8
            prediction_diffs.append(diff);predictions += 1
            calculated.append([actual,predicted,train[:,1].mean(),last,0.])
        data = np.array(calculated)
        assert len(data) == walk["n_predictions"]
        for col,method in enumerate(("ridge","historical_mean","last_change","zero_change"),1):
            errors = data[:,col]-data[:,0]
            sign = lambda a: np.where(np.abs(a)<=1e-12,0,np.sign(a))
            values = {"mae":np.abs(errors).mean(),"rmse":np.sqrt((errors**2).mean()),
                      "directional_accuracy":(sign(data[:,col])==sign(data[:,0])).mean()}
            for key,value in values.items():
                diff=abs(float(value)-walk["metrics"][method][key]);assert diff < 1e-8
                metric_diffs.append(diff);metrics += 1
    vacancy = research["derived_private_vacancy_rate"]
    for row in vacancy["observations"]:
        expected = Decimal(str(row["vacant_units"])) / Decimal(str(row["total_units"])) * 100
        assert abs(expected-Decimal(str(row["value"]))) < Decimal("1e-8")
    selected = read(root / "selection.json")
    assert len(selected["decisions"]) == len(candidates)
    assert all(d["reason_origin"]=="model" for d in selected["decisions"])
    language_files = ("report.md","report.html","indicator_pool.md","indicator_pool.html","indicator_pool.json")
    assert all(not re.search(r"[\u3400-\u9fff]",(root/n).read_text()) for n in language_files)
    return {"schema_version":1,"run":root.name,"status":"passed",
            "manifest_sha256":hashlib.sha256((root/"manifest.json").read_bytes()).hexdigest(),
            "method":"Original SingStat cell/period checks; Decimal changes; independent NumPy Pearson correlations and ridge matrix solves.",
            "inventoried_files_checked":len(manifest["files"]),"raw_observations_checked":count,
            "latest_changes_checked":len(formula_differences),"correlations_checked":correlations,
            "ridge_predictions_checked":predictions,"metric_values_checked":metrics,
            "vacancy_rates_checked":len(vacancy["observations"]),"english_presentation_files_checked":list(language_files),
            "max_absolute_differences":{"latest_changes":max(formula_differences,default=0),
            "correlations":max(corr_diffs,default=0),"ridge_predictions":max(prediction_diffs,default=0),
            "metrics":max(metric_diffs,default=0)},
            "limitations":"Arithmetic and captured-data integrity checks do not validate causal explanations, publication-time availability or future predictive accuracy."}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path);parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise SystemExit("Audit output must be a new file.")
    result=audit(args.run.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps(result,indent=2))
