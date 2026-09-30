"""Run and replay the full, auditable workflow."""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import date
from importlib.resources import files
from pathlib import Path

from . import __version__
from .engine import evaluate_series, select_candidates
from .report import render_html, render_report
from .sources import SingStatClient, fetch_series
from .storage import file_inventory, read_json, sha256_bytes, utc_now, verify_inventory, write_json

AS_OF_POLICY = "Latest downloaded vintage filtered by observation reference date (or period end); not a historical point-in-time information set."


def load_local_environment() -> None:
    path = Path.cwd() / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep and key.strip() in {"OPENAI_API_KEY", "OPENAI_MODEL"}:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value:
                os.environ.setdefault(key.strip(), value)


def failure_evaluation(spec: dict, error: str) -> dict:
    return {"id": f"{spec['table_id']}:{spec['row_id']}", "metadata": {"name": spec["expected_name"], "theme": spec["theme"]},
            "latest": None, "changes": [], "observations": [],
            "quality": {"eligible": False, "score": 0, "reasons": [error], "warnings": [], "missing_fraction": 1, "valid_count": 0}}


def export_processed(path: Path, series_list: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["series_id", "period", "observation_date", "value", "unit", "raw_period", "raw_value", "raw_index", "raw_file", "raw_sha256"])
        writer.writeheader()
        for series in series_list:
            for obs in series["observations"]:
                writer.writerow({"series_id": series["id"], "period": obs["period"], "observation_date": obs.get("observation_date", ""), "value": obs["value"], "unit": series["unit"], "raw_period": obs["raw_period"], "raw_value": obs["raw_value"], "raw_index": obs["raw_index"], **{k: series["provenance"][k] for k in ["raw_file", "raw_sha256"]}})


def run_workflow(as_of: str, output: Path, mode: str = "rules", limit: int = 5, model: str | None = None, timeout: float = 20, progress=print) -> dict:
    date.fromisoformat(as_of)
    if not 1 <= limit <= 12:
        raise ValueError("Selection limit must be between 1 and 12")
    if timeout <= 0:
        raise ValueError("HTTP timeout must be positive")
    load_local_environment()
    if mode == "llm" and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not configured. Fill local .env or explicitly use --mode rules.")
    if mode == "llm" and not (model or os.environ.get("OPENAI_MODEL")):
        raise ValueError("Set OPENAI_MODEL in .env or pass --model with a tool-capable model available to your API project.")
    if mode not in {"rules", "llm"}:
        raise ValueError("Unknown analysis mode")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    run = {"schema_version": 1, "run_id": output.name, "created_at": utc_now(), "as_of": as_of,
           "as_of_policy": AS_OF_POLICY, "mode": mode,
           "mode_label": "Deterministic rules; reviewed qualitative templates, no model call" if mode == "rules" else "Live OpenAI tool-calling agent",
           "data_basis": AS_OF_POLICY, "package_version": __version__, "python_version": sys.version.split()[0],
           "warnings": [], "status": "running"}
    try:
        git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parent, capture_output=True, text=True, timeout=5)
        run["code_commit"] = git.stdout.strip() if git.returncode == 0 else "not in git checkout"
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=Path(__file__).resolve().parent, capture_output=True, text=True, timeout=5)
        run["code_worktree_dirty"] = bool(dirty.stdout.strip()) if dirty.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        run["code_commit"] = "unavailable"
    source_dir = Path(__file__).resolve().parent
    run["code_hashes"] = {str(p.relative_to(source_dir)): sha256_bytes(p.read_bytes()) for p in sorted(source_dir.glob("*.py"))}
    write_json(output / "manifest.json", run)
    client = SingStatClient(output, timeout=timeout)
    try:
        import json
        catalogue = json.loads(files("housing_agent").joinpath("data/catalogue.json").read_text(encoding="utf-8"))
        if isinstance(catalogue, dict):
            catalogue = catalogue["candidates"]
        write_json(output / "catalogue.json", catalogue)
        discoveries = []
        for query in ["population", "gross domestic product", "unemployment", "income", "interest rates", "loans", "residential properties", "consumer price"]:
            progress(f"Discovering official tables: {query}")
            try:
                records = client.discover(query)
                discoveries.append({"query": query, "records": records, "status": "ok"})
            except Exception as exc:
                discoveries.append({"query": query, "status": "failed", "error": str(exc)})
                run["warnings"].append(f"Official catalogue query failed for {query}; reviewed candidate identifiers were still attempted.")
        write_json(output / "discovery.json", discoveries)
        series_list, evaluations = [], []
        for spec in catalogue:
            progress(f"Fetching and evaluating: {spec['expected_name']}")
            try:
                series = fetch_series(client, spec)
                evaluation = evaluate_series(series, as_of)
                series_list.append(series)
                evaluations.append(evaluation)
            except Exception as exc:
                evaluations.append(failure_evaluation(spec, str(exc)))
                run["warnings"].append(f"Excluded {spec['table_id']}:{spec['row_id']} after retrieval or validation failure: {exc}")
        client.save_records()
        write_json(output / "normalized.json", series_list)
        write_json(output / "evaluations.json", evaluations)
        export_processed(output / "processed.csv", [
            {**item["metadata"], "id": item["id"], "observations": item["observations"]}
            for item in evaluations if "provenance" in item["metadata"]
        ])
        if not any(item["quality"]["eligible"] for item in evaluations):
            raise ValueError("No candidate passes data quality gates; inspect evaluations.json and retrievals.json. No report fabricated.")
        progress("Selecting indicators from actual candidate evaluations")
        if mode == "llm":
            from .agent import run_agent
            selection = run_agent(evaluations, as_of, limit, model or os.environ["OPENAI_MODEL"], output / "agent_trace.json")
        else:
            selection = select_candidates(evaluations, limit)
            selection["narratives"] = {e["id"]: {**e["metadata"]["mechanism"], "evidence_ids": [e["id"] + ":latest"]} for e in evaluations if e["id"] in selection["selected_ids"]}
            selection["usage"] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        if not selection["selected_ids"]:
            raise ValueError("Selection is empty; no report generated")
        eligible = {x["id"] for x in evaluations if x["quality"]["eligible"]}
        selected_ids = selection["selected_ids"]
        if len(selected_ids) != len(set(selected_ids)) or not set(selected_ids) <= eligible or len(selected_ids) > limit:
            raise ValueError("Selection violates candidate eligibility, uniqueness or size constraints")
        if len(selected_ids) < limit:
            run["warnings"].append("Selected fewer candidates than requested; missing slots were not filled with ineligible series.")
        write_json(output / "selection.json", selection)
        run["selected_ids"] = selected_ids
        run["model"] = model or os.environ.get("OPENAI_MODEL") if mode == "llm" else None
        run["usage"] = selection.get("usage", {})
        run["status"] = "complete_with_warnings" if run["warnings"] else "complete"
        write_json(output / "report_context.json", run)
        report = render_report(run, evaluations, selection)
        (output / "report.md").write_text(report, encoding="utf-8")
        (output / "report.html").write_text(render_html(report), encoding="utf-8")
        run["files"] = file_inventory(output)
        write_json(output / "manifest.json", run)
        progress(f"Report saved: {output / 'report.md'}")
        return run
    except Exception as exc:
        client.save_records()
        run.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        run["files"] = file_inventory(output)
        write_json(output / "manifest.json", run)
        raise


def replay(run_dir: Path, output: Path) -> dict:
    run_dir = run_dir.resolve()
    manifest = read_json(run_dir / "manifest.json")
    if not manifest.get("status", "").startswith("complete"):
        raise ValueError("Cannot replay a failed or incomplete run")
    verify_inventory(run_dir, manifest)
    if output.exists() or output.resolve().is_relative_to(run_dir):
        raise ValueError("Replay output must be a new file outside the immutable source run")
    report = render_report(read_json(run_dir / "report_context.json"), read_json(run_dir / "evaluations.json"), read_json(run_dir / "selection.json"))
    if report.encode() != (run_dir / "report.md").read_bytes():
        raise ValueError("Current renderer differs from the saved report; use the recorded code version for exact replay")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {"verified_files": len(manifest["files"]), "report": str(output), "sha256": sha256_bytes(report.encode()), "network_calls": 0, "model_calls": 0}
