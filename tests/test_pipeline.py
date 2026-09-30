"""End-to-end failure, reproducibility and immutable-artifact contracts."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from housing_agent.engine import evaluate_series, select_candidates
from housing_agent.pipeline import load_local_environment, replay, run_workflow
from housing_agent.report import render_report
from housing_agent.storage import file_inventory, read_json, sha256_bytes, write_json


def specimen(spec):
    identifier = f"{spec['table_id']}:{spec['row_id']}"
    return {"id": identifier, "name": spec["expected_name"], "theme": spec["theme"], "definition": spec["definition"],
            "unit": "Number", "frequency": "A", "update_frequency": "Annual; inferred", "source_url": "https://tablebuilder.singstat.gov.sg/",
            "table_id": spec["table_id"], "row_id": spec["row_id"], "source_agency": "Test fixture, not a real downloaded value",
            "retrieved_at": "2026-10-01T00:00:00Z", "source_updated_at": "unknown", "change_kind": "percent",
            "mechanism": {"sales": "Demand may support purchases.", "rents": "Demand may support rentals.", "lag": "Timing may vary.", "limitations": "No causal claim."},
            "provenance": {"raw_file": "raw/test.json", "raw_sha256": "fixture", "metadata_file": "raw/meta.json", "metadata_sha256": "fixture"},
            "observations": [{"period": str(y), "value": 100 + y - 2020, "raw_period": str(y), "raw_value": str(100 + y - 2020), "raw_index": y - 2020} for y in range(2020, 2026)]}


class PipelineTests(unittest.TestCase):
    def test_processed_export_respects_report_date(self):
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "historical"
            with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), patch("housing_agent.pipeline.fetch_series", side_effect=lambda client, spec: specimen(spec)):
                run_workflow("2023-12-31", root, progress=lambda _: None)
            with (root / "processed.csv").open() as fh:
                rows = list(csv.DictReader(fh))
            self.assertTrue(rows)
            self.assertTrue(all(int(row["period"]) <= 2023 for row in rows))
            # Full downloaded history remains available separately, never destroyed.
            self.assertEqual(read_json(root / "normalized.json")[0]["observations"][-1]["period"], "2025")

    def test_missing_comparison_does_not_split_markdown_table(self):
        from importlib.resources import files
        spec = json.loads(files("housing_agent").joinpath("data/catalogue.json").read_text())[0]
        series = specimen(spec)
        series["frequency"] = "Q"
        series["observations"] = [{"period": f"{year}-Q{quarter}", "value": 100 + year - 2020 + quarter} for year in range(2020, 2024) for quarter in range(1, 5) if (year, quarter) != (2023, 3)]
        evaluation = evaluate_series(series, "2023-12-31")
        selection = select_candidates([evaluation], 1)
        context = {"as_of": "2023-12-31", "run_id": "test", "created_at": "test", "mode_label": "fixture", "data_basis": "synthetic", "warnings": []}
        report = render_report(context, [evaluation], selection)
        self.assertIn("| previous_period", report)
        self.assertIn("| year_on_year", report)
        self.assertGreater(report.index("Calculation limitation:"), report.index("| year_on_year"))

    def test_complete_workflow_replay_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def captured_source(client, spec):
                obj = specimen(spec)
                write_json(client.run_dir / "raw/test.json", {"note": "Synthetic test fixture"})
                write_json(client.run_dir / "raw/meta.json", {"note": "Synthetic test metadata"})
                return obj
            with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), patch("housing_agent.pipeline.fetch_series", side_effect=captured_source):
                result = run_workflow("2026-09-30", root / "run", progress=lambda _: None)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(len(result["selected_ids"]), 5)
            out = root / "replayed.md"
            with patch("urllib.request.urlopen", side_effect=AssertionError("Replay must be offline")):
                info = replay(root / "run", out)
            self.assertEqual(info["network_calls"], 0)
            self.assertEqual(out.read_bytes(), (root / "run/report.md").read_bytes())
            (root / "run/raw/test.json").write_text('{"tampered": true}')
            with self.assertRaisesRegex(ValueError, "Missing or changed"):
                replay(root / "run", root / "tampered.md")

    def test_all_downloads_fail_leaves_failed_record_and_no_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "failed"
            with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=RuntimeError("offline")), patch("housing_agent.pipeline.fetch_series", side_effect=RuntimeError("schema changed")):
                with self.assertRaisesRegex(ValueError, "No candidate"):
                    run_workflow("2026-09-30", root, progress=lambda _: None)
            self.assertEqual(read_json(root / "manifest.json")["status"], "failed")
            self.assertEqual(len(read_json(root / "evaluations.json")), 12)
            self.assertFalse((root / "report.md").exists())

    def test_partial_failure_never_selects_failed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "partial"
            def fetch(client, spec):
                if spec["table_id"] == "M810001":
                    raise RuntimeError("source unavailable")
                return specimen(spec)
            with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), patch("housing_agent.pipeline.fetch_series", side_effect=fetch):
                result = run_workflow("2026-09-30", root, progress=lambda _: None)
            self.assertEqual(result["status"], "complete_with_warnings")
            self.assertTrue(all(not i.startswith("M810001") for i in result["selected_ids"]))
            self.assertIn("source unavailable", (root / "report.md").read_text())

    def test_existing_run_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sentinel = root / "precious.txt"
            sentinel.write_text("keep")
            with self.assertRaises(FileExistsError):
                run_workflow("2026-09-30", root)
            self.assertEqual(sentinel.read_text(), "keep")

    def test_missing_key_fails_before_downloading(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch("housing_agent.pipeline.load_local_environment"), patch("housing_agent.pipeline.fetch_series") as fetch:
            output = Path(tmp) / "run"
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                run_workflow("2026-09-30", output, mode="llm")
            fetch.assert_not_called()
            self.assertFalse(output.exists())

    def test_manifest_path_traversal_is_rejected(self):
        from housing_agent.storage import verify_inventory
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Unsafe path"):
                verify_inventory(Path(tmp), {"files": {"../outside": "hash"}})

    def test_local_env_is_not_executed_and_environment_wins(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"OPENAI_MODEL": "existing"}, clear=True), patch("pathlib.Path.cwd", return_value=Path(tmp)):
            (Path(tmp) / ".env").write_text('OPENAI_API_KEY="test-local-only"\nOPENAI_MODEL=ignored\nUNRELATED_SECRET=never_load\n')
            load_local_environment()
            self.assertEqual(os.environ["OPENAI_API_KEY"], "test-local-only")
            self.assertEqual(os.environ["OPENAI_MODEL"], "existing")
            self.assertNotIn("UNRELATED_SECRET", os.environ)


if __name__ == "__main__":
    unittest.main()
