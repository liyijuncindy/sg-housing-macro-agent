"""End-to-end failure, reproducibility and immutable-artifact contracts."""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from housing_agent.engine import evaluate_series, select_candidates
from housing_agent.pipeline import load_local_environment, replay, run_workflow as _run_workflow
from housing_agent.report import render_report
from housing_agent.storage import file_inventory, read_json, sha256_bytes, write_json


def run_workflow(*args, **kwargs):
    # These original tests exercise the single-source protocol with synthetic fixtures.
    # The independent-source default and failure isolation have their own integration tests.
    kwargs.setdefault("source_policy", "singstat")
    return _run_workflow(*args, **kwargs)


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
    def setUp(self):
        # Existing rules tests must never read the user's real environment file.
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        loader = patch("housing_agent.pipeline.load_local_environment")
        loader.start()
        self.addCleanup(loader.stop)

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
            self.assertEqual(len(read_json(root / "evaluations.json")), len(read_json(root / "catalogue.json")))
            self.assertFalse((root / "report.md").exists())

    def test_unused_capacity_reports_actual_eligible_count_without_blame_on_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), patch("housing_agent.pipeline.fetch_series", side_effect=lambda client, spec: specimen(spec)), patch("housing_agent.pipeline.select_candidates", side_effect=lambda evaluations, limit: select_candidates(evaluations, 1)):
                result = run_workflow("2026-10-01", root, limit=5, progress=lambda _: None)
            self.assertEqual(result["status"], "complete_with_warnings")
            count = result["source_coverage"]["eligible"]
            self.assertGreater(count, 5)
            self.assertIn(f"Selected 1 of {count} eligible candidates", result["warnings"][0])
            self.assertIn("does not by itself imply", result["warnings"][0])
            self.assertIn("no backup sources enabled", result["source_strategy"])

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

    def test_selection_limit_is_a_positive_integer_bounded_by_the_run_catalogue(self):
        from importlib.resources import files
        count = len(json.loads(files("housing_agent").joinpath("data/catalogue.json").read_text()))
        with tempfile.TemporaryDirectory() as tmp:
            for value in (False, True, 0, -1, 1.5, count + 1):
                output = Path(tmp) / str(value)
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, "limit"):
                    run_workflow("2026-10-01", output, limit=value)
                self.assertFalse(output.exists())

    def test_missing_key_fails_before_downloading(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True), patch("housing_agent.pipeline.load_local_environment"), patch("housing_agent.pipeline.fetch_series") as fetch:
            output = Path(tmp) / "run"
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
                run_workflow("2026-09-30", output, mode="llm")
            fetch.assert_not_called()
            self.assertFalse(output.exists())

    def test_historical_reports_still_replay_without_provider_configuration(self):
        examples = Path(__file__).resolve().parents[1] / "examples"
        names = ("sample_run", "soclaas_verified_run", "independent_sources_run",
                 "singstat_priority_agent_run", "singstat_priority_verified_run", "singstat_priority_rules_run")
        with tempfile.TemporaryDirectory() as tmp, \
                patch("housing_agent.agent.run_agent", side_effect=AssertionError("Replay must not call a provider")), \
                patch("housing_agent.sources.urlopen", side_effect=AssertionError("Replay must not fetch sources")):
            for name in names:
                with self.subTest(run=name):
                    output = Path(tmp) / (name + ".md")
                    result = replay(examples / name, output)
                    self.assertEqual(output.read_bytes(), (examples / name / "report.md").read_bytes())
                    self.assertEqual(result["network_calls"], 0)
                    self.assertEqual(result["model_calls"], 0)

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


class ProviderPipelineTests(unittest.TestCase):
    """Provider routing contracts with synthetic credentials and offline data."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.next_run = 0
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        current_directory = patch("pathlib.Path.cwd", return_value=self.root)
        current_directory.start()
        self.addCleanup(current_directory.stop)
        discovery = patch("housing_agent.pipeline.SingStatClient.discover", return_value=[])
        self.discover = discovery.start()
        self.addCleanup(discovery.stop)
        fetcher = patch("housing_agent.pipeline.fetch_series", side_effect=lambda client, spec: specimen(spec))
        self.fetch = fetcher.start()
        self.addCleanup(fetcher.stop)
        agent = patch("housing_agent.agent.run_agent", side_effect=self.completed_selection)
        self.agent = agent.start()
        self.addCleanup(agent.stop)
        # Unexpected source calls fail locally; tests never make network requests.
        network = patch("housing_agent.sources.urlopen", side_effect=AssertionError("Tests are offline"))
        network.start()
        self.addCleanup(network.stop)

    @staticmethod
    def completed_selection(evaluations, as_of, limit, model, trace_path, **kwargs):
        selection = select_candidates(evaluations, limit)
        selection["method"] = "Mocked provider completion, not a live LLM call"
        selection["usage"] = {"input_tokens": 50, "output_tokens": 30, "total_tokens": 80, "requests": 1}
        # A replay must preserve the provider trace just like other captured files.
        write_json(trace_path, {"status": "completed", "provider": kwargs.get("provider"),
                                "model": model, "actual_models": [model], "elapsed_seconds": 0.25,
                                "usage": selection["usage"]})
        return selection

    def output_path(self):
        self.next_run += 1
        return self.root / f"run-{self.next_run}"

    def run_llm(self, **kwargs):
        output = self.output_path()
        result = run_workflow("2026-09-30", output, mode="llm", progress=lambda _: None, **kwargs)
        return result, output

    def configure_providers(self):
        os.environ.update({"OPENAI_API_KEY": "synthetic-openai-key",
                           "OPENAI_MODEL": "openai-test-model",
                           "SOCLAAS_API_KEY": "synthetic-soclaas-key",
                           "SOCLAAS_MODEL": "soclaas-test-model",
                           "SILICONFLOW_API_KEY": "synthetic-siliconflow-key",
                           "SILICONFLOW_MODEL": "zai-org/GLM-5.3"})

    def assert_preflight_failure(self, required_message, **kwargs):
        output = self.output_path()
        self.discover.reset_mock()
        self.fetch.reset_mock()
        self.agent.reset_mock()
        with self.assertRaisesRegex(ValueError, required_message):
            run_workflow("2026-09-30", output, mode="llm", progress=lambda _: None, **kwargs)
        self.discover.assert_not_called()
        self.fetch.assert_not_called()
        self.agent.assert_not_called()
        self.assertFalse(output.exists())

    def test_explicit_provider_and_model_override_environment_and_are_recorded(self):
        self.configure_providers()
        os.environ["LLM_PROVIDER"] = "openai"
        result, output = self.run_llm(provider="soclaas", model="explicit-test-model")
        self.assertEqual(result["provider"], "soclaas")
        self.assertEqual(result["model"], "explicit-test-model")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "soclaas")
        self.assertEqual(self.agent.call_args.args[3], "explicit-test-model")
        self.assertEqual(result["usage"], {"input_tokens": 50, "output_tokens": 30, "total_tokens": 80, "requests": 1})
        self.assertIsInstance(result["elapsed_seconds"], (float, int))
        self.assertGreaterEqual(result["elapsed_seconds"], 0)
        manifest = read_json(output / "manifest.json")
        self.assertEqual(manifest["provider"], result["provider"])
        self.assertEqual(manifest["model"], result["model"])
        self.assertEqual(manifest["usage"], result["usage"])
        self.assertEqual(manifest["elapsed_seconds"], result["elapsed_seconds"])
        self.assertTrue((output / "report.md").is_file())
        self.assertTrue((output / "report.html").is_file())
        # Credentials belong in the local environment, never saved artifacts.
        for path in output.rglob("*"):
            if path.is_file():
                body = path.read_text(encoding="utf-8")
                self.assertNotIn("synthetic-openai-key", body)
                self.assertNotIn("synthetic-soclaas-key", body)

    def test_environment_selects_soclaas_and_uses_only_its_model(self):
        self.configure_providers()
        os.environ["LLM_PROVIDER"] = "soclaas"
        result, _ = self.run_llm()
        self.assertEqual(result["provider"], "soclaas")
        self.assertEqual(result["model"], "soclaas-test-model")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "soclaas")
        self.assertEqual(self.agent.call_args.args[3], "soclaas-test-model")

    def test_siliconflow_provider_model_and_mode_are_recorded_without_credential_leakage(self):
        self.configure_providers()
        os.environ["LLM_PROVIDER"] = "openai"
        result, output = self.run_llm(provider="siliconflow", model="zai-org/GLM-5.3")
        expected_label = "Live SiliconFlow Chat Completions tool-calling agent (zai-org/GLM-5.3)"
        self.assertEqual(self.agent.call_args.kwargs["provider"], "siliconflow")
        self.assertEqual(self.agent.call_args.args[3], "zai-org/GLM-5.3")
        for artifact in (result, read_json(output / "manifest.json"), read_json(output / "report_context.json")):
            self.assertEqual(artifact["provider"], "siliconflow")
            self.assertEqual(artifact["model"], "zai-org/GLM-5.3")
            self.assertEqual(artifact["actual_models"], ["zai-org/GLM-5.3"])
            self.assertEqual(artifact["mode_label"], expected_label)
            self.assertEqual(artifact["agent_elapsed_seconds"], 0.25)
        self.assertIn(expected_label, (output / "report.md").read_text())
        self.assertEqual(read_json(output / "agent_trace.json")["provider"], "siliconflow")
        for path in output.rglob("*"):
            if path.is_file():
                body = path.read_text(encoding="utf-8")
                for secret in ("synthetic-openai-key", "synthetic-soclaas-key", "synthetic-siliconflow-key"):
                    self.assertNotIn(secret, body)

    def test_environment_selects_siliconflow_and_uses_only_its_model(self):
        self.configure_providers()
        os.environ["LLM_PROVIDER"] = "siliconflow"
        result, _ = self.run_llm()
        self.assertEqual(result["provider"], "siliconflow")
        self.assertEqual(result["model"], "zai-org/GLM-5.3")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "siliconflow")

    def test_cli_accepts_siliconflow_and_forwards_explicit_model(self):
        from housing_agent.__main__ import main
        output = self.output_path()
        summary = {"status": "complete", "provider": "siliconflow", "model": "zai-org/GLM-5.3"}
        with patch("housing_agent.pipeline.run_workflow", return_value=summary) as workflow, \
                patch("sys.stdout", new_callable=io.StringIO) as stdout:
            code = main(["run", "--as-of", "2026-10-01", "--output", str(output),
                         "--mode", "llm", "--provider", "siliconflow", "--model", "zai-org/GLM-5.3"])
        self.assertEqual(code, 0)
        self.assertEqual(workflow.call_args.kwargs["provider"], "siliconflow")
        self.assertEqual(workflow.call_args.args[4], "zai-org/GLM-5.3")
        self.assertEqual(json.loads(stdout.getvalue())["provider"], "siliconflow")
        self.agent.assert_not_called()

    def test_discovery_maintenance_does_not_prevent_working_candidate_tables_or_model(self):
        from housing_agent.sources import SourceMaintenanceError
        self.configure_providers()
        self.discover.side_effect = SourceMaintenanceError("This request returned a current maintenance page")
        output = self.output_path()
        result = run_workflow("2026-09-30", output, mode="llm", provider="soclaas", progress=lambda _: None)
        count = len(read_json(output / "catalogue.json"))
        self.assertGreater(self.discover.call_count, 1)
        self.assertEqual(self.fetch.call_count, count)
        self.agent.assert_called_once()
        self.assertTrue((output / "report.md").exists())
        self.assertEqual(result["source_coverage"]["downloaded"], count)
        self.assertTrue(result["source_coverage"]["maintenance_responses_observed"])
        self.assertEqual(read_json(output / "discovery.json")[0]["status"], "failed")

    def test_all_series_maintenance_rechecks_every_candidate_before_failing_without_model(self):
        from housing_agent.sources import SourceMaintenanceError
        self.configure_providers()
        self.fetch.side_effect = SourceMaintenanceError("This request returned a current maintenance page")
        output = self.output_path()
        with self.assertRaisesRegex(ValueError, "No candidate"):
            run_workflow("2026-09-30", output, mode="llm", provider="soclaas", progress=lambda _: None)
        count = len(read_json(output / "catalogue.json"))
        self.assertEqual(self.fetch.call_count, count * 2)
        self.agent.assert_not_called()
        self.assertFalse((output / "report.md").exists())
        manifest = read_json(output / "manifest.json")
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(len(manifest["source_coverage"]["unavailable"]), count)
        self.assertEqual(manifest["usage"]["total_tokens"], 0)
        routes = read_json(output / "source_routes.json")
        self.assertTrue(all(len(route["attempts"]) == 2 for route in routes))

    def test_default_provider_is_openai_when_no_provider_is_supplied(self):
        self.configure_providers()
        result, _ = self.run_llm()
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "openai-test-model")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "openai")

    def test_explicit_openai_overrides_soclaas_environment(self):
        self.configure_providers()
        os.environ["LLM_PROVIDER"] = "soclaas"
        result, _ = self.run_llm(provider="openai")
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "openai-test-model")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "openai")

    def test_other_provider_key_is_never_a_fallback(self):
        for provider, prefix in [("openai", "OPENAI"), ("soclaas", "SOCLAAS"), ("siliconflow", "SILICONFLOW")]:
            with self.subTest(provider=provider):
                self.configure_providers()
                del os.environ[prefix + "_API_KEY"]
                self.assert_preflight_failure(prefix + "_API_KEY", provider=provider)

    def test_other_provider_model_is_never_a_fallback(self):
        for provider, prefix in [("openai", "OPENAI"), ("soclaas", "SOCLAAS"), ("siliconflow", "SILICONFLOW")]:
            with self.subTest(provider=provider):
                self.configure_providers()
                del os.environ[prefix + "_MODEL"]
                self.assert_preflight_failure(prefix + "_MODEL", provider=provider)

    def test_explicit_model_can_supply_missing_provider_model(self):
        os.environ.update({"SOCLAAS_API_KEY": "synthetic-soclaas-key",
                           "OPENAI_MODEL": "unrelated-openai-model"})
        result, _ = self.run_llm(provider="soclaas", model="command-model")
        self.assertEqual(result["model"], "command-model")
        self.assertEqual(self.agent.call_args.args[3], "command-model")

    def test_invalid_provider_fails_before_data_or_output(self):
        self.configure_providers()
        self.assert_preflight_failure("(?i)provider", provider="untrusted-proxy")
        os.environ["LLM_PROVIDER"] = "unknown-provider"
        self.assert_preflight_failure("(?i)provider")

    def test_local_file_only_loads_supported_keys_and_environment_wins(self):
        os.environ.update({"LLM_PROVIDER": "openai", "SOCLAAS_MODEL": "shell-model",
                           "SILICONFLOW_MODEL": "shell-siliconflow-model"})
        (self.root / ".env").write_text(
            'LLM_PROVIDER=soclaas\nSOCLAAS_API_KEY="local-test-key"\n'
            "SOCLAAS_MODEL=file-model\nOPENAI_API_KEY='local-openai-test-key'\n"
            "OPENAI_MODEL=file-openai-model\n"
            "SILICONFLOW_API_KEY=local-siliconflow-test-key\n"
            "SILICONFLOW_MODEL=zai-org/GLM-5.3\n"
            "SOCLAAS_BASE_URL=https://untrusted.invalid\n"
            "OPENAI_BASE_URL=https://untrusted.invalid\n"
            "SILICONFLOW_BASE_URL=https://untrusted.invalid\n"
            "UNRELATED_SECRET=must-not-load\n")
        load_local_environment()
        self.assertEqual(os.environ["LLM_PROVIDER"], "openai")
        self.assertEqual(os.environ["SOCLAAS_MODEL"], "shell-model")
        self.assertEqual(os.environ["SOCLAAS_API_KEY"], "local-test-key")
        self.assertEqual(os.environ["OPENAI_API_KEY"], "local-openai-test-key")
        self.assertEqual(os.environ["OPENAI_MODEL"], "file-openai-model")
        self.assertEqual(os.environ["SILICONFLOW_API_KEY"], "local-siliconflow-test-key")
        self.assertEqual(os.environ["SILICONFLOW_MODEL"], "shell-siliconflow-model")
        for name in ["SOCLAAS_BASE_URL", "OPENAI_BASE_URL", "SILICONFLOW_BASE_URL", "UNRELATED_SECRET"]:
            self.assertNotIn(name, os.environ)

    def test_provider_from_local_file_is_used_by_workflow(self):
        (self.root / ".env").write_text(
            "LLM_PROVIDER=soclaas\nSOCLAAS_API_KEY=local-synthetic-key\nSOCLAAS_MODEL=local-test-model\n")
        result, _ = self.run_llm()
        self.assertEqual(result["provider"], "soclaas")
        self.assertEqual(result["model"], "local-test-model")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "soclaas")

    def test_siliconflow_configuration_from_local_file_is_used_by_workflow(self):
        (self.root / ".env").write_text(
            "LLM_PROVIDER=siliconflow\nSILICONFLOW_API_KEY=local-synthetic-key\nSILICONFLOW_MODEL=zai-org/GLM-5.3\n")
        result, _ = self.run_llm()
        self.assertEqual(result["provider"], "siliconflow")
        self.assertEqual(result["model"], "zai-org/GLM-5.3")
        self.assertEqual(self.agent.call_args.kwargs["provider"], "siliconflow")

    def test_environment_template_recommends_siliconflow_without_removing_other_providers(self):
        text = (Path(__file__).resolve().parents[1] / ".env.example").read_text()
        values = dict(line.split("=", 1) for line in text.splitlines() if line and not line.startswith("#"))
        self.assertEqual(values["LLM_PROVIDER"], "siliconflow")
        self.assertEqual(values["SILICONFLOW_MODEL"], "zai-org/GLM-5.3")
        for provider in ("OPENAI", "SOCLAAS", "SILICONFLOW"):
            self.assertEqual(values[provider + "_API_KEY"], "")
            self.assertTrue(values[provider + "_MODEL"])

    def test_rules_mode_needs_no_provider_credentials_or_model_call(self):
        os.environ["LLM_PROVIDER"] = "soclaas"
        output = self.output_path()
        result = run_workflow("2026-09-30", output, progress=lambda _: None)
        self.assertEqual(result["mode"], "rules")
        self.assertIsNone(result["model"])
        self.assertEqual(result["usage"]["total_tokens"], 0)
        self.agent.assert_not_called()
        self.assertTrue((output / "report.md").is_file())

    def test_provider_runs_replay_without_credentials_or_provider_calls(self):
        for provider in ("openai", "soclaas", "siliconflow"):
            with self.subTest(provider=provider):
                self.configure_providers()
                os.environ["LLM_PROVIDER"] = provider
                result, source = self.run_llm()
                self.assertEqual(result["provider"], provider)
                os.environ.clear()
                self.agent.reset_mock()
                self.discover.reset_mock()
                self.fetch.reset_mock()
                destination = self.root / (provider + "-offline-replayed.md")
                information = replay(source, destination)
                self.assertEqual(information["network_calls"], 0)
                self.assertEqual(information["model_calls"], 0)
                self.assertEqual(destination.read_bytes(), (source / "report.md").read_bytes())
                self.agent.assert_not_called()
                self.discover.assert_not_called()
                self.fetch.assert_not_called()


class SavedSourcePipelineTests(unittest.TestCase):
    """A verified source capture can feed a new live model call without refresh."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = patch.dict(os.environ, {"SOCLAAS_API_KEY": "synthetic-saved-source-key",
                                               "SOCLAAS_MODEL": "saved-source-model"}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        current_directory = patch("pathlib.Path.cwd", return_value=self.root)
        current_directory.start()
        self.addCleanup(current_directory.stop)
        self.source = self.root / "original-capture"
        self.source.mkdir()
        from importlib.resources import files
        specs = json.loads(files("housing_agent").joinpath("data/catalogue.json").read_text())[:2]
        self.available_id = f"{specs[0]['table_id']}:{specs[0]['row_id']}"
        self.missing_id = f"{specs[1]['table_id']}:{specs[1]['row_id']}"
        series = specimen(specs[0])
        write_json(self.source / "raw/test.json", {"note": "Synthetic saved source observations"})
        write_json(self.source / "raw/meta.json", {"note": "Synthetic saved source metadata"})
        series["provenance"]["raw_sha256"] = sha256_bytes((self.source / "raw/test.json").read_bytes())
        series["provenance"]["metadata_sha256"] = sha256_bytes((self.source / "raw/meta.json").read_bytes())
        write_json(self.source / "catalogue.json", specs)
        write_json(self.source / "normalized.json", [series])
        write_json(self.source / "discovery.json", [{"query": "population", "status": "ok", "records": []}])
        write_json(self.source / "retrievals.json", [{"status": "ok", "retrieved_at": series["retrieved_at"],
                    "raw_file": series["provenance"]["raw_file"], "raw_sha256": series["provenance"]["raw_sha256"]}])
        # These files are hashed, but must never be used as new model output.
        write_json(self.source / "agent_trace.json", {"old_agent_output": "must-not-copy"})
        write_json(self.source / "selection.json", {"old_selection": "must-not-copy"})
        (self.source / "report.md").write_text("Old report must not be copied")
        self.refresh_source_manifest()
        discovery = patch("housing_agent.pipeline.SingStatClient.discover", side_effect=AssertionError("No SingStat discovery"))
        self.discover = discovery.start()
        self.addCleanup(discovery.stop)
        fetch = patch("housing_agent.pipeline.fetch_series", side_effect=AssertionError("No source download"))
        self.fetch = fetch.start()
        self.addCleanup(fetch.stop)
        agent = patch("housing_agent.agent.run_agent", side_effect=ProviderPipelineTests.completed_selection)
        self.agent = agent.start()
        self.addCleanup(agent.stop)
        network = patch("housing_agent.sources.urlopen", side_effect=AssertionError("No source network"))
        self.network = network.start()
        self.addCleanup(network.stop)

    def refresh_source_manifest(self):
        write_json(self.source / "manifest.json", {"status": "complete_with_warnings",
                   "run_id": self.source.name, "created_at": "2026-10-01T00:00:00Z",
                   "files": file_inventory(self.source)})

    def run_saved(self, as_of="2023-12-31", name="new-run"):
        output = self.root / name
        result = run_workflow(as_of, output, mode="llm", provider="soclaas", source_run=self.source,
                              limit=2, progress=lambda _: None)
        return result, output

    def assert_no_source_calls(self):
        self.discover.assert_not_called()
        self.fetch.assert_not_called()
        self.network.assert_not_called()

    def assert_invalid_source(self, pattern="."):
        output = self.root / "rejected-run"
        with self.assertRaisesRegex((ValueError, OSError), pattern):
            run_workflow("2023-12-31", output, mode="llm", provider="soclaas", source_run=self.source,
                         progress=lambda _: None)
        self.assertFalse(output.exists())
        self.agent.assert_not_called()
        self.assert_no_source_calls()

    def test_verified_snapshot_drives_new_model_call_and_recalculates_cutoff(self):
        source_manifest_hash = sha256_bytes((self.source / "manifest.json").read_bytes())
        original_inventory = file_inventory(self.source)
        original_mtime = (self.source / "raw/test.json").stat().st_mtime_ns
        result, output = self.run_saved()
        self.assert_no_source_calls()
        self.agent.assert_called_once()
        self.assertEqual(self.agent.call_args.kwargs["provider"], "soclaas")
        evaluations = self.agent.call_args.args[0]
        captured = next(item for item in evaluations if item["id"] == self.available_id)
        self.assertEqual(captured["latest"]["period"], "2023")
        self.assertTrue(all(int(row["period"]) <= 2023 for row in captured["observations"]))
        self.assertEqual(read_json(output / "normalized.json")[0]["observations"][-1]["period"], "2025")
        missing = next(item for item in evaluations if item["id"] == self.missing_id)
        self.assertFalse(missing["quality"]["eligible"])
        self.assertIn("absent", missing["quality"]["reasons"][0])
        self.assertNotIn(self.missing_id, result["selected_ids"])
        self.assertEqual(result["source_run"]["name"], self.source.name)
        self.assertEqual(result["source_run"]["manifest_sha256"], source_manifest_hash)
        self.assertEqual(result["source_run"]["original_created_at"], "2026-10-01T00:00:00Z")
        self.assertIn("No new source refresh", result["data_basis"])
        self.assertIn("2026-10-01", result["data_basis"])
        self.assertTrue(any("saved source snapshot" in item for item in result["warnings"]))
        self.assertEqual(result["usage"]["total_tokens"], 80)
        for name in ["catalogue.json", "normalized.json", "discovery.json", "retrievals.json", "raw/test.json", "raw/meta.json"]:
            self.assertEqual((output / name).read_bytes(), (self.source / name).read_bytes())
        self.assertEqual((output / "raw/test.json").stat().st_mtime_ns, original_mtime)
        self.assertEqual(file_inventory(self.source), original_inventory)
        self.assertNotIn("old_agent_output", read_json(output / "agent_trace.json"))
        self.assertNotIn("old_selection", read_json(output / "selection.json"))
        self.assertNotIn("Old report must not be copied", (output / "report.md").read_text())
        replayed = self.root / "saved-source-replay.md"
        replay(output, replayed)
        self.assertEqual(replayed.read_bytes(), (output / "report.md").read_bytes())
        self.assertEqual(self.agent.call_count, 1)

    def test_changed_source_data_is_rejected_before_new_run_or_model(self):
        (self.source / "normalized.json").write_text("[]")
        self.assert_invalid_source("Missing or changed")

    def test_inventory_checks_prior_non_source_artifacts_too(self):
        (self.source / "report.md").write_text("Changed old report")
        self.assert_invalid_source("Missing or changed")

    def test_incomplete_source_run_is_rejected_before_new_run_or_model(self):
        manifest = read_json(self.source / "manifest.json")
        manifest["status"] = "failed"
        write_json(self.source / "manifest.json", manifest)
        self.assert_invalid_source("must be complete")

    def test_canonical_artifacts_must_be_in_inventory_even_if_files_exist(self):
        for filename in ["normalized.json", "catalogue.json", "discovery.json", "retrievals.json"]:
            with self.subTest(filename=filename):
                self.refresh_source_manifest()
                manifest = read_json(self.source / "manifest.json")
                del manifest["files"][filename]
                write_json(self.source / "manifest.json", manifest)
                self.assert_invalid_source("inventory")

    def test_raw_provenance_cannot_point_to_uninventoried_file(self):
        manifest = read_json(self.source / "manifest.json")
        del manifest["files"]["raw/test.json"]
        write_json(self.source / "manifest.json", manifest)
        self.assert_invalid_source("raw provenance")

    def test_raw_provenance_hash_must_match_manifest(self):
        normalized = read_json(self.source / "normalized.json")
        normalized[0]["provenance"]["raw_sha256"] = "not-the-captured-hash"
        write_json(self.source / "normalized.json", normalized)
        self.refresh_source_manifest()
        self.assert_invalid_source("raw provenance")

    def test_failed_response_prefix_hash_must_match_manifest(self):
        retrievals = read_json(self.source / "retrievals.json")
        retrievals[0]["attempts"] = [{"error_body_prefix_file": "raw/test.json",
                                      "error_body_prefix_sha256": "not-the-captured-hash"}]
        write_json(self.source / "retrievals.json", retrievals)
        self.refresh_source_manifest()
        self.assert_invalid_source("raw provenance")

    def test_saved_source_cannot_be_modified_by_nested_output(self):
        output = self.source / "nested-new-run"
        with self.assertRaisesRegex(ValueError, "outside the immutable"):
            run_workflow("2023-12-31", output, mode="llm", provider="soclaas", source_run=self.source,
                         progress=lambda _: None)
        self.assertFalse(output.exists())
        self.agent.assert_not_called()
        self.assert_no_source_calls()


if __name__ == "__main__":
    unittest.main()
