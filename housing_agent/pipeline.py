"""Run and replay the full, auditable workflow."""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import time
from datetime import date
from importlib.resources import files
from pathlib import Path

from . import __version__
from .engine import evaluate_series, select_candidates
from .indicator_pool import build_indicator_pool, write_indicator_pool
from .report import render_html, render_report
from .sources import SingStatClient, SourceMaintenanceError, fetch_series
from .official_sources import OfficialFileClient, DIRECT_IDS
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
        if sep and key.strip() in {"OPENAI_API_KEY", "OPENAI_MODEL", "LLM_PROVIDER", "SOCLAAS_API_KEY", "SOCLAAS_MODEL"}:
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
        writer = csv.DictWriter(fh, fieldnames=["series_id", "period", "observation_date", "published_at", "source_value_date", "source_publication_date", "value", "unit", "raw_period", "raw_value", "raw_index", "raw_locator", "preliminary", "raw_file", "raw_sha256"])
        writer.writeheader()
        for series in series_list:
            for obs in series["observations"]:
                writer.writerow({"series_id": series["id"], "period": obs["period"], "observation_date": obs.get("observation_date", ""), "value": obs["value"], "unit": series["unit"], "raw_period": obs["raw_period"], "raw_value": obs["raw_value"], "raw_index": obs["raw_index"], **{k: obs.get(k, "") for k in ("published_at", "source_value_date", "source_publication_date", "raw_locator", "preliminary")}, **{k: series["provenance"][k] for k in ["raw_file", "raw_sha256"]}})


def _saved_source(source_run: Path, output: Path) -> dict:
    """Verify a complete capture before creating a new run or making any calls."""
    root = source_run.resolve()
    if output.is_relative_to(root):
        raise ValueError("New output must be outside the immutable source run")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("status") not in {"complete", "complete_with_warnings"}:
        raise ValueError("Saved source run must be complete")
    inventory = manifest.get("files")
    required = {"catalogue.json", "normalized.json", "discovery.json", "retrievals.json"}
    if not isinstance(inventory, dict) or not required <= set(inventory):
        raise ValueError("Saved source inventory must list catalogue.json, normalized.json, discovery.json and retrievals.json")
    verify_inventory(root, manifest)
    catalogue = read_json(root / "catalogue.json")
    normalized = read_json(root / "normalized.json")
    discoveries = read_json(root / "discovery.json")
    retrievals = read_json(root / "retrievals.json")
    if not all(isinstance(value, list) for value in (catalogue, normalized, discoveries, retrievals)) or not catalogue:
        raise ValueError("Saved source artifacts must contain lists and a nonempty catalogue")
    expected = [f"{item['table_id']}:{item['row_id']}" for item in catalogue]
    if len(expected) != len(set(expected)):
        raise ValueError("Saved source catalogue contains duplicate series")
    by_id = {}
    for series in normalized:
        if not isinstance(series, dict) or series.get("id") not in expected or series["id"] in by_id:
            raise ValueError("Saved normalized data contains an unknown or duplicate series")
        by_id[series["id"]] = series

    def require_raw(relative, expected_hash):
        if (not isinstance(relative, str) or not relative.startswith("raw/")
                or any(part in {".", ".."} for part in relative.split("/"))
                or relative not in inventory or inventory[relative] != expected_hash):
            raise ValueError("Saved source raw provenance is missing from its verified inventory")

    for series in normalized:
        provenance = series.get("provenance", {})
        require_raw(provenance.get("raw_file"), provenance.get("raw_sha256"))
        require_raw(provenance.get("metadata_file"), provenance.get("metadata_sha256"))
    for record in retrievals:
        if not isinstance(record, dict):
            raise ValueError("Saved retrieval records must be objects")
        if record.get("raw_file") is not None:
            require_raw(record["raw_file"], record.get("raw_sha256"))
    raw_files = {name for name in inventory if name.startswith("raw/")}
    for name in raw_files:
        require_raw(name, inventory[name])
    captured_at = sorted({series["retrieved_at"] for series in normalized
                          if isinstance(series.get("retrieved_at"), str) and series["retrieved_at"]})
    provenance = {"name": root.name, "manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
                  "original_created_at": manifest.get("created_at"),
                  "retrieved_at_min": captured_at[0] if captured_at else None,
                  "retrieved_at_max": captured_at[-1] if captured_at else None}
    return {"root": root, "catalogue": catalogue, "by_id": by_id,
            "files": sorted(required | raw_files), "provenance": provenance}


def run_workflow(as_of: str, output: Path, mode: str = "rules", limit: int = 5, model: str | None = None, timeout: float = 20, progress=print, provider: str | None = None, source_run: Path | None = None, source_policy: str = "auto") -> dict:
    started = time.monotonic()
    date.fromisoformat(as_of)
    if not 1 <= limit <= 12:
        raise ValueError("Selection limit must be between 1 and 12")
    if timeout <= 0:
        raise ValueError("HTTP timeout must be positive")
    if source_policy not in {"auto", "singstat"}:
        raise ValueError("Unknown source policy; choose auto or singstat")
    load_local_environment()
    if mode not in {"rules", "llm"}:
        raise ValueError("Unknown analysis mode")
    if mode == "llm":
        provider = provider or os.environ.get("LLM_PROVIDER", "openai")
        if provider not in {"openai", "soclaas"}:
            raise ValueError("Unknown LLM provider; choose openai or soclaas")
        prefix = provider.upper()
        if not os.environ.get(f"{prefix}_API_KEY", "").strip():
            raise ValueError(f"{prefix}_API_KEY is not configured. Fill local .env or explicitly use --mode rules.")
        model = (model or os.environ.get(f"{prefix}_MODEL", "")).strip()
        if not model:
            raise ValueError(f"Set {prefix}_MODEL in .env or pass --model with a tool-capable model available to this provider.")
    else:
        provider, model = None, None
    output = output.resolve()
    saved = _saved_source(source_run, output) if source_run is not None else None
    output.mkdir(parents=True, exist_ok=False)
    run = {"schema_version": 1, "run_id": output.name, "created_at": utc_now(), "as_of": as_of,
           "as_of_policy": AS_OF_POLICY, "mode": mode,
           "mode_label": "Deterministic rules; reviewed qualitative templates, no model call" if mode == "rules" else f"Live {'SoCLaaS Chat Completions' if provider == 'soclaas' else 'OpenAI Responses'} tool-calling agent ({model})",
           "provider": provider, "model": model, "source_policy": "saved" if saved else source_policy,
           "data_basis": AS_OF_POLICY, "package_version": __version__, "python_version": sys.version.split()[0],
           "warnings": [], "status": "running",
           "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}}
    if saved is not None:
        run["source_run"] = saved["provenance"]
        capture = saved["provenance"]["retrieved_at_min"] or saved["provenance"]["original_created_at"] or "unknown capture time"
        note = (f"Verified saved source snapshot from {saved['root'].name}, captured from {capture}; "
                "original retrieval timestamps are preserved. No new source refresh was performed.")
        run["data_basis"] = note + " " + AS_OF_POLICY.replace("Latest downloaded vintage", "Saved captured vintage")
        run["warnings"].append(note)
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
    client = SingStatClient(output, timeout=timeout) if saved is None else None
    official_client = OfficialFileClient(output, timeout=timeout) if saved is None and source_policy == "auto" else None
    maintenance_error = None

    def save_retrievals():
        if client is not None:
            records = client.records + (official_client.records if official_client is not None else [])
            write_json(output / "retrievals.json", sorted(records, key=lambda item: item["retrieved_at"]))

    try:
        if saved is None:
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
                except SourceMaintenanceError as exc:
                    discoveries.append({"query": query, "status": "maintenance", "error": str(exc)})
                    write_json(output / "discovery.json", discoveries)
                    if source_policy == "singstat":
                        raise
                    maintenance_error = str(exc)
                    run["warnings"].append("SingStat Table Builder is under maintenance; remaining searches and SingStat-only candidates were skipped. Independent MOM and MAS downloads were still attempted.")
                    break
                except Exception as exc:
                    discoveries.append({"query": query, "status": "failed", "error": str(exc)})
                    run["warnings"].append(f"Official catalogue query failed for {query}; reviewed candidate identifiers were still attempted.")
            write_json(output / "discovery.json", discoveries)
        else:
            progress(f"Using verified saved source snapshot: {saved['root'].name}")
            catalogue = saved["catalogue"]
            for relative in saved["files"]:
                destination = output / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(saved["root"] / relative, destination)
        series_list, evaluations = [], []
        for spec in catalogue:
            progress(f"{'Fetching and evaluating' if saved is None else 'Re-evaluating saved source'}: {spec['expected_name']}")
            try:
                if saved is None:
                    identifier = f"{spec['table_id']}:{spec['row_id']}"
                    if official_client is not None and identifier in DIRECT_IDS:
                        if identifier == "M700071:23":
                            from .mas_sources import fetch_mas_series
                            series = fetch_mas_series(official_client, spec, as_of)
                        else:
                            from .mom_sources import fetch_mom_series
                            series = fetch_mom_series(official_client, spec)
                    elif maintenance_error is not None:
                        raise ValueError("SingStat source skipped after confirmed maintenance; no supported independent route for this candidate. " + maintenance_error)
                    else:
                        series = fetch_series(client, spec)
                else:
                    identifier = f"{spec['table_id']}:{spec['row_id']}"
                    if identifier not in saved["by_id"]:
                        raise ValueError("Series is absent from the verified saved snapshot; no replacement was downloaded")
                    series = saved["by_id"][identifier]
                evaluation = evaluate_series(series, as_of)
                series_list.append(series)
                evaluations.append(evaluation)
            except SourceMaintenanceError as exc:
                if source_policy == "singstat":
                    raise
                maintenance_error = str(exc)
                evaluations.append(failure_evaluation(spec, str(exc)))
                run["warnings"].append(f"Excluded {spec['table_id']}:{spec['row_id']}: SingStat maintenance; independent sources continue.")
            except Exception as exc:
                evaluations.append(failure_evaluation(spec, str(exc)))
                run["warnings"].append(f"Excluded {spec['table_id']}:{spec['row_id']} after retrieval or validation failure: {exc}")
        if client is not None:
            save_retrievals()
            write_json(output / "normalized.json", series_list)
        run["source_coverage"] = {"candidates": len(catalogue), "downloaded": len(series_list),
                                  "eligible": sum(bool(item["quality"]["eligible"]) for item in evaluations),
                                  "singstat_maintenance": maintenance_error is not None,
                                  "providers": sorted({item.get("source_provider", "SingStat Table Builder") for item in series_list})}
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
            selection = run_agent(evaluations, as_of, limit, model, output / "agent_trace.json", provider=provider)
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
        run["usage"] = selection.get("usage", {})
        if mode == "llm":
            trace = read_json(output / "agent_trace.json") if (output / "agent_trace.json").exists() else {}
            run["actual_models"] = trace.get("actual_models", [])
            run["agent_elapsed_seconds"] = trace.get("elapsed_seconds")
        run["status"] = "complete_with_warnings" if run["warnings"] else "complete"
        run["finished_at"] = utc_now()
        run["elapsed_seconds"] = round(time.monotonic() - started, 3)
        run["indicator_pool_files"] = {"markdown": "indicator_pool.md", "html": "indicator_pool.html", "json": "indicator_pool.json"}
        write_indicator_pool(output, build_indicator_pool(run, catalogue, evaluations, selection))
        write_json(output / "report_context.json", run)
        report = render_report(run, evaluations, selection)
        (output / "report.md").write_text(report, encoding="utf-8")
        (output / "report.html").write_text(render_html(report), encoding="utf-8")
        run["files"] = file_inventory(output)
        write_json(output / "manifest.json", run)
        progress(f"Report saved: {output / 'report.md'}")
        return run
    except Exception as exc:
        save_retrievals()
        run.update(status="failed", error=f"{type(exc).__name__}: {exc}", finished_at=utc_now(),
                   elapsed_seconds=round(time.monotonic() - started, 3))
        if isinstance(exc, SourceMaintenanceError):
            run["failure_category"] = "source_maintenance"
            run["recovery"] = "Retry a new run after SingStat maintenance ends, or explicitly use --source-run with a verified saved snapshot. No source fallback was automatic."
            run["usage"] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "requests": 0}
        if (output / "agent_trace.json").exists():
            trace = read_json(output / "agent_trace.json")
            run["usage"] = trace.get("usage", {})
            run["actual_models"] = trace.get("actual_models", [])
            run["agent_elapsed_seconds"] = trace.get("elapsed_seconds")
        run["files"] = file_inventory(output)
        write_json(output / "manifest.json", run)
        raise


def export_indicator_pool(run_dir: Path, output: Path) -> dict:
    """Present verified saved decisions; never refresh data or reselect indicators."""
    root, output = run_dir.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError("Indicator pool output must be a new directory outside the immutable source run")
    manifest_path = root / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("status") not in {"complete", "complete_with_warnings"}:
        raise ValueError("Indicator pool export requires a complete source run")
    required = {"catalogue.json", "evaluations.json", "selection.json", "report_context.json"}
    if not required <= set(manifest.get("files", {})):
        raise ValueError("Indicator pool inputs must be listed in the source run inventory")
    verify_inventory(root, manifest)
    pool = build_indicator_pool(read_json(root / "report_context.json"), read_json(root / "catalogue.json"),
                                read_json(root / "evaluations.json"), read_json(root / "selection.json"))
    exported = {"artifact_type": "indicator_pool_export", "schema_version": 1, "status": "complete",
                "exported_at": utc_now(), "source_run": root.name,
                "source_manifest_sha256": sha256_bytes(manifest_path.read_bytes()),
                "source_input_hashes": {name: manifest["files"][name] for name in sorted(required)},
                "network_calls": 0, "model_calls": 0,
                "note": "Presentation of saved observations and decisions; no data refresh or new selection."}
    pool["export_provenance"] = exported.copy()
    output.mkdir(parents=True, exist_ok=False)
    write_indicator_pool(output, pool)
    exported["files"] = file_inventory(output)
    write_json(output / "manifest.json", exported)
    return exported


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
