"""The table preserves saved decisions and the immutable-run audit boundary."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from housing_agent.pipeline import export_indicator_pool, replay, run_workflow
from housing_agent.storage import read_json, sha256_bytes, verify_inventory, write_json


SOURCE = Path(__file__).resolve().parents[1] / "examples/independent_sources_run"


class IndicatorPoolIntegrationTests(unittest.TestCase):
    def test_saved_export_keeps_source_files_and_selection_unchanged_offline(self):
        original = {str(p.relative_to(SOURCE)): sha256_bytes(p.read_bytes())
                    for p in SOURCE.rglob("*") if p.is_file()}
        with tempfile.TemporaryDirectory() as tmp, \
                patch("urllib.request.urlopen", side_effect=AssertionError("Export must be offline")), \
                patch("housing_agent.agent.run_agent", side_effect=AssertionError("Export must not call a model")):
            output = Path(tmp) / "pool"
            result = export_indicator_pool(SOURCE, output)
            self.assertEqual(result["network_calls"], 0)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["source_manifest_sha256"], original["manifest.json"])
            self.assertEqual(set(result["files"]), {"indicator_pool.md", "indicator_pool.html", "indicator_pool.json"})
            verify_inventory(output, result)
            pool = read_json(output / "indicator_pool.json")
            self.assertEqual(len(pool["rows"]), 12)
            saved = read_json(SOURCE / "selection.json")
            # Exact reasons survive the Chinese presentation, including maintenance details.
            def strings(value):
                if isinstance(value, str):
                    yield value
                elif isinstance(value, dict):
                    for nested in value.values():
                        yield from strings(nested)
                elif isinstance(value, list):
                    for nested in value:
                        yield from strings(nested)
            saved_strings = set(strings(pool))
            for decision in saved["decisions"]:
                self.assertIn(decision["reason"], saved_strings)
        self.assertEqual(original, {str(p.relative_to(SOURCE)): sha256_bytes(p.read_bytes())
                                   for p in SOURCE.rglob("*") if p.is_file()})

    def test_export_rejects_tampering_and_uninventoried_inputs_before_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for scenario in ("tampered", "uninventoried"):
                with self.subTest(scenario=scenario):
                    source = root / scenario
                    shutil.copytree(SOURCE, source)
                    if scenario == "tampered":
                        (source / "selection.json").write_text("{}", encoding="utf-8")
                    else:
                        manifest = read_json(source / "manifest.json")
                        del manifest["files"]["selection.json"]
                        write_json(source / "manifest.json", manifest)
                    output = root / (scenario + "-output")
                    with self.assertRaises(ValueError):
                        export_indicator_pool(source, output)
                    self.assertFalse(output.exists())

    def test_export_does_not_overwrite_or_modify_source_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            for output in (Path(tmp), SOURCE / "new-table"):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, "new directory outside"):
                    export_indicator_pool(SOURCE, output)

    def test_new_workflow_inventories_table_and_replays_without_breaking_old_reports(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch("housing_agent.pipeline.load_local_environment"), \
                patch("urllib.request.urlopen", side_effect=AssertionError("Saved run must be offline")):
            root = Path(tmp)
            result = run_workflow("2026-10-01", root / "run", source_run=SOURCE, progress=lambda _: None)
            for name in ("indicator_pool.json", "indicator_pool.md", "indicator_pool.html"):
                self.assertIn(name, result["files"])
            self.assertIn("[可搜索的表格预览](indicator_pool.html)", (root / "run/report.md").read_text())
            self.assertIn('href="indicator_pool.html"', (root / "run/report.html").read_text())
            replay(root / "run", root / "new-replayed.md")
            self.assertEqual((root / "new-replayed.md").read_bytes(), (root / "run/report.md").read_bytes())
            for example in ("sample_run", "soclaas_verified_run", "independent_sources_run"):
                replay(SOURCE.parent / example, root / (example + ".md"))


if __name__ == "__main__":
    unittest.main()
