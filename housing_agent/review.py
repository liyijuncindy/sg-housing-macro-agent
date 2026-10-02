"""Create a labelled, offline editorial presentation without altering a source run."""
from copy import deepcopy
from pathlib import Path
import re
import shutil

from .indicator_pool import build_indicator_pool, write_indicator_pool
from .report import render_report, render_html
from .storage import read_json, write_json, utc_now, sha256_bytes, verify_inventory, file_inventory


def _text(value):
    if not isinstance(value, str) or not value.strip() or re.search(r"[\u3400-\u9fff]", value):
        raise ValueError("Editorial corrections must be nonempty English text")
    return value.strip()


def review_report(run_dir: Path, review_file: Path, output: Path) -> dict:
    root, output = run_dir.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError("Reviewed output must be a new directory outside the immutable source run")
    manifest = read_json(root / "manifest.json")
    if not manifest.get("status", "").startswith("complete"):
        raise ValueError("Editorial review requires a completed source run")
    verify_inventory(root, manifest)
    required = {"report_context.json", "selection.json", "evaluations.json", "catalogue.json", "research.json"}
    if not required <= set(manifest["files"]):
        raise ValueError("Editorial review inputs must be inventoried in the source run")
    run = read_json(root / "report_context.json")
    if run.get("report_version") != 2:
        raise ValueError("Editorial review requires an English report v2 source")
    review_bytes = review_file.read_bytes()
    review = read_json(review_file)
    if set(review) != {"summary", "decision_edits", "narrative_edits", "notes"}:
        raise ValueError("Review must contain summary, decision_edits, narrative_edits and notes")
    _text(review["summary"])
    if not isinstance(review["notes"], list) or any(not isinstance(n,str) or not n.strip() for n in review["notes"]):
        raise ValueError("Review notes must be a list of nonempty strings")
    for note in review["notes"]:
        _text(note)
    if not isinstance(review["decision_edits"], dict) or not isinstance(review["narrative_edits"], dict):
        raise ValueError("Editorial edits must be objects keyed by candidate ID")
    original = read_json(root / "selection.json")
    selection = deepcopy(original)
    decisions = {d["id"]:d for d in selection["decisions"]}
    for key, reason in review["decision_edits"].items():
        if key not in decisions:
            raise ValueError("Editorial decision contains an unknown candidate")
        decisions[key].update(reason=_text(reason), reason_origin="editorial_review",
                              original_model_reason=decisions[key]["reason"])
    allowed = {"sales", "rents", "lag", "limitations"}
    for key, edits in review["narrative_edits"].items():
        if not isinstance(edits, dict) or key not in selection["narratives"] or not set(edits) <= allowed:
            raise ValueError("Editorial narrative contains an unknown candidate or unsupported field")
        for field, value in edits.items():
            selection["narratives"][key][field] = _text(value)
    selection["editorial_review"] = review
    selection["usage"] = {"input_tokens":0,"output_tokens":0,"total_tokens":0,"requests":0}
    now = utc_now()
    run.update(artifact_type="editorially_reviewed_report", run_id=output.name, created_at=now,
               finished_at=now, mode_label=f"Editorially reviewed presentation of {root.name}; no new model or source calls",
               original_model_usage=deepcopy(run["usage"]),
               usage={"input_tokens":0,"output_tokens":0,"total_tokens":0,"requests":0},
               source_execution={"run":root.name,"manifest_sha256":sha256_bytes((root/"manifest.json").read_bytes()),
                                 "created_at":manifest["created_at"],"code_commit":manifest.get("code_commit")},
               report_fields_version=2,
               editorial_review={"summary":review["summary"],"decision_edits":len(review["decision_edits"]),
                                 "narrative_edits":sum(len(fields) for fields in review["narrative_edits"].values()),
                                 "review_file":"selection_review.json","original_selection":"original_selection.json",
                                 "input_review_sha256":sha256_bytes(review_bytes)},
               network_calls=0, model_calls=0, elapsed_seconds=0, agent_elapsed_seconds=0)
    run["source_policy"] = "reviewed_saved"
    run["source_strategy"] = "Verified artifacts copied from the original execution; no new retrieval or selection."
    run["data_basis"] = "Editorial presentation of the verified original capture; no source refresh. " + run["data_basis"]
    run["outcome_coverage"]["freshly_retrieved"] = False
    run["presentation_code_hashes"] = {p.name:sha256_bytes(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))}
    output.mkdir(parents=True, exist_ok=False)
    # Copy only inventoried artifacts. Every generated image and raw response
    # keeps its original hash; the source remains untouched.
    for name in manifest["files"]:
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/name,target)
    write_json(output/"original_selection.json",original)
    write_json(output/"selection_review.json",review)
    write_json(output/"selection.json",selection)
    write_indicator_pool(output,build_indicator_pool(run,read_json(output/"catalogue.json"),read_json(output/"evaluations.json"),selection))
    write_json(output/"report_context.json",run)
    markdown=render_report(run,read_json(output/"evaluations.json"),selection)
    (output/"report.md").write_text(markdown,encoding="utf-8")
    (output/"report.html").write_text(render_html(markdown,output),encoding="utf-8")
    run["files"]=file_inventory(output);write_json(output/"manifest.json",run)
    return run
