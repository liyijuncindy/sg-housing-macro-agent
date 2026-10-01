"""Transport boundaries and mixed-source failure isolation; no live requests."""
import io
import os
from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from housing_agent.official_sources import DIRECT_IDS, OfficialFileClient, SourceError, _OfficialRedirects
from housing_agent.pipeline import run_workflow, replay
from housing_agent.sources import SourceMaintenanceError, SourceUnavailableError
from housing_agent.storage import read_json, sha256_bytes, write_json
from tests.test_pipeline import specimen


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Type": "text/csv", "Last-Modified": "Thu, 01 Oct 2026 00:00:00 GMT"}

    def geturl(self):
        return "https://stats.mom.gov.sg/public.csv"


class OfficialTransportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.client = OfficialFileClient(self.root)

    def test_raw_download_and_form_identity_are_audited(self):
        body = b"quarter,value\n2026-Q2,2.9\n"
        with patch.object(self.client.opener, "open", return_value=Response(body)) as opening:
            downloaded, record = self.client.download("https://stats.mom.gov.sg/public.csv", name="test", suffix=".csv", data=b"field=value")
        self.assertEqual(downloaded, body)
        self.assertEqual((self.root / record["raw_file"]).read_bytes(), body)
        self.assertEqual(record["raw_sha256"], sha256_bytes(body))
        self.assertEqual(record["request_body_sha256"], sha256_bytes(b"field=value"))
        self.assertEqual(record["method"], "POST")
        self.assertIn("http_last_modified", record)
        self.assertNotIn("published_at", record)
        self.assertEqual(opening.call_args.args[0].data, b"field=value")

    def test_temporary_gateway_failure_is_bounded_and_recorded(self):
        error = HTTPError("https://stats.mom.gov.sg/public.csv", 502, "gateway", {}, io.BytesIO())
        with patch.object(self.client.opener, "open", side_effect=[error, Response(b"ok")]) as opening, patch("housing_agent.official_sources.time.sleep"):
            _, record = self.client.download("https://stats.mom.gov.sg/public.csv", name="test", suffix=".csv")
        self.assertEqual(opening.call_count, 2)
        self.assertEqual([item["status"] for item in record["attempts"]], ["failed", "ok"])

    def test_permanent_error_and_oversize_do_not_retry(self):
        error = HTTPError("https://stats.mom.gov.sg/public.csv", 404, "missing", {}, io.BytesIO())
        with patch.object(self.client.opener, "open", side_effect=error) as opening:
            with self.assertRaises(SourceError):
                self.client.download("https://stats.mom.gov.sg/public.csv", name="test", suffix=".csv")
        self.assertEqual(opening.call_count, 1)
        with patch("housing_agent.official_sources.MAX_BYTES", 3), patch.object(self.client.opener, "open", return_value=Response(b"1234")) as opening:
            with self.assertRaisesRegex(SourceError, "size limit"):
                self.client.download("https://stats.mom.gov.sg/public.csv", name="test", suffix=".csv")
        self.assertEqual(opening.call_count, 1)

    def test_unreviewed_hosts_and_redirects_and_credential_headers_are_rejected(self):
        for url in ["http://stats.mom.gov.sg/a", "https://example.com/a", "https://user:secret@stats.mom.gov.sg/a"]:
            with self.subTest(url=url), self.assertRaises(SourceError):
                self.client.download(url, name="test", suffix=".csv")
        with self.assertRaises(SourceError):
            _OfficialRedirects().redirect_request(None, None, 302, "", {}, "https://example.com/file")
        with self.assertRaises(SourceError):
            self.client.download("https://stats.mom.gov.sg/a", name="test", suffix=".csv", headers={"Authorization": "synthetic"})

    def test_adapter_metadata_is_distinguished_and_cannot_be_overwritten(self):
        record = self.client.metadata("test", {"source_url": "https://stats.mom.gov.sg/a"})
        self.assertIn("not an official", read_json(self.root / record["raw_file"])["metadata_origin"])
        self.assertEqual(record["raw_sha256"], sha256_bytes((self.root / record["raw_file"]).read_bytes()))
        with self.assertRaisesRegex(SourceError, "overwrite"):
            self.client.metadata("test", {})

    def test_partial_http_response_is_never_accepted_as_complete_history(self):
        response = Response(b"period,value\n2026-Q2,2.9\n")
        response.status = 206
        with patch.object(self.client.opener, "open", return_value=response) as opening:
            with self.assertRaisesRegex(SourceError, "complete HTTP 200"):
                self.client.download("https://stats.mom.gov.sg/public.csv", name="partial", suffix=".csv")
        self.assertEqual(opening.call_count, 1)
        self.assertEqual(self.client.records[0]["status"], "failed")
        self.assertNotIn("raw_file", self.client.records[0])


class MultiSourcePipelineTests(unittest.TestCase):
    """SingStat-first routing, isolated failures and explicit audited fallback."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for guard in (
            patch("housing_agent.pipeline.load_local_environment"),
            patch.dict(os.environ, {}, clear=True),
            patch("housing_agent.sources.urlopen", side_effect=AssertionError("Tests must not make source requests")),
            patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Tests must not make file requests")),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    @staticmethod
    def identifier(spec):
        return f"{spec['table_id']}:{spec['row_id']}"

    def captured(self, client, spec, provider):
        series = specimen(spec)
        token = self.identifier(spec).replace(":", "_").replace(".", "_")
        raw = client.run_dir / "raw" / f"{provider}_{token}.json"
        metadata = client.run_dir / "raw" / f"{provider}_{token}_metadata.json"
        write_json(raw, {"note": "Synthetic test observations, not official data"})
        write_json(metadata, {"note": "Synthetic test metadata, not official data"})
        host = {"SingStat": "tablebuilder.singstat.gov.sg", "MOM": "stats.mom.gov.sg", "MAS": "eservices.mas.gov.sg"}[provider]
        source_url = f"https://{host}/synthetic/{token}"
        record = {"url": source_url, "retrieved_at": series["retrieved_at"],
                  "status": "ok", "attempts": [{"status": "ok"}],
                  "raw_file": str(raw.relative_to(client.run_dir)), "raw_sha256": sha256_bytes(raw.read_bytes())}
        client.records.append(record)
        series.update(source_provider=f"Synthetic {provider} fixture", source_url=source_url)
        series["provenance"] = {"raw_file": record["raw_file"], "raw_sha256": record["raw_sha256"],
                                "metadata_file": str(metadata.relative_to(client.run_dir)),
                                "metadata_sha256": sha256_bytes(metadata.read_bytes())}
        for observation in series["observations"]:
            observation["raw_locator"] = "Synthetic JSON observation"
        return series

    def captured_primary(self, client, spec):
        return self.captured(client, spec, "SingStat")

    def captured_direct(self, client, spec, *args):
        return self.captured(client, spec, "MAS" if self.identifier(spec) == "M700071:23" else "MOM")

    def catalogue_ids(self, output):
        return [self.identifier(spec) for spec in read_json(output / "catalogue.json")]

    def routes(self, output):
        records = read_json(output / "source_routes.json")
        self.assertEqual([item["id"] for item in records], self.catalogue_ids(output))
        for record in records:
            self.assertEqual(record["primary_source"], "SingStat")
            self.assertIn(record["status"], {"ok", "failed"})
            self.assertIn(record["used_source"], {"SingStat", "MOM", "MAS", None})
            self.assertTrue(record["attempts"])
            for attempt in record["attempts"]:
                self.assertIn(attempt["stage"], {"primary", "primary_recheck", "fallback"})
                self.assertIn(attempt["provider"], {"SingStat", "MOM", "MAS"})
                self.assertIn(attempt["status"], {"ok", "failed"})
                self.assertTrue(attempt["checked_at"])
                if attempt["status"] == "failed":
                    self.assertTrue(attempt["error"])
                    self.assertIsInstance(attempt["retryable"], bool)
        return {record["id"]: record for record in records}

    def assert_candidate_coverage(self, output):
        self.assertEqual([item["id"] for item in read_json(output / "evaluations.json")], self.catalogue_ids(output))

    def test_all_primary_success_uses_singstat_and_never_direct_sources(self):
        output = self.root / "primary"
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                patch("housing_agent.pipeline.fetch_series", side_effect=self.captured_primary) as singstat, \
                patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series") as mas:
            result = run_workflow("2026-10-01", output, progress=lambda _: None)
        ids = self.catalogue_ids(output)
        self.assertEqual([self.identifier(call.args[1]) for call in singstat.call_args_list], ids)
        mom.assert_not_called()
        mas.assert_not_called()
        self.assert_candidate_coverage(output)
        for route in self.routes(output).values():
            self.assertEqual((route["status"], route["used_source"]), ("ok", "SingStat"))
            self.assertEqual([(a["stage"], a["status"]) for a in route["attempts"]], [("primary", "ok")])
        self.assertEqual(result["source_policy"], "auto")
        self.assertEqual(result["source_coverage"]["singstat_downloaded"], len(ids))
        self.assertEqual(result["source_coverage"]["fallback_downloaded"], 0)
        self.assertEqual(result["source_coverage"]["maintenance_responses_observed"], 0)
        self.assertNotIn("singstat_maintenance", result["source_coverage"])

    def test_discovery_maintenance_or_gateway_failure_does_not_skip_other_queries_or_candidates(self):
        for number, error in enumerate((SourceMaintenanceError("Maintenance response on a search endpoint"),
                                        SourceUnavailableError("HTTP 502 on a search endpoint"))):
            with self.subTest(error=type(error).__name__):
                output = self.root / f"query-error-{number}"
                with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=error) as discover, \
                        patch("housing_agent.pipeline.fetch_series", side_effect=self.captured_primary) as singstat, \
                        patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                        patch("housing_agent.mas_sources.fetch_mas_series") as mas:
                    result = run_workflow("2026-10-01", output, progress=lambda _: None)
                self.assertGreater(discover.call_count, 1)
                discoveries = read_json(output / "discovery.json")
                self.assertEqual(len(discoveries), discover.call_count)
                self.assertTrue(all(item["status"] != "ok" and item["error"] for item in discoveries))
                self.assertEqual([self.identifier(call.args[1]) for call in singstat.call_args_list], self.catalogue_ids(output))
                self.assert_candidate_coverage(output)
                self.assertEqual(result["source_coverage"]["singstat_downloaded"], len(self.catalogue_ids(output)))
                self.assertEqual(result["source_coverage"]["fallback_downloaded"], 0)
                mom.assert_not_called()
                mas.assert_not_called()
                self.assertTrue(all(route["used_source"] == "SingStat" for route in self.routes(output).values()))

    def test_retryable_primary_failure_is_rechecked_after_other_candidates_before_fallback(self):
        target = "M182342:2"
        for number, error in enumerate((SourceMaintenanceError("Temporary maintenance for this table"),
                                        SourceUnavailableError("Temporary HTTP 502"))):
            with self.subTest(error=type(error).__name__):
                output = self.root / f"recovered-{number}"
                calls = []
                def primary(client, spec):
                    identifier = self.identifier(spec)
                    calls.append(identifier)
                    if identifier == target and calls.count(target) == 1:
                        raise error
                    return self.captured_primary(client, spec)
                with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                        patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                        patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                        patch("housing_agent.mas_sources.fetch_mas_series") as mas:
                    result = run_workflow("2026-10-01", output, progress=lambda _: None)
                self.assertEqual(calls, self.catalogue_ids(output) + [target])
                mom.assert_not_called()
                mas.assert_not_called()
                route = self.routes(output)[target]
                self.assertEqual(route["used_source"], "SingStat")
                self.assertEqual([(a["stage"], a["status"]) for a in route["attempts"]],
                                 [("primary", "failed"), ("primary_recheck", "ok")])
                self.assertTrue(route["attempts"][0]["retryable"])
                self.assertIn(str(error), route["attempts"][0]["error"])
                self.assertEqual(result["source_coverage"]["fallback_downloaded"], 0)

    def test_permanent_failure_is_not_rechecked_and_only_that_candidate_uses_fallback(self):
        target = "M184101:1"
        output = self.root / "one-fallback"
        def primary(client, spec):
            if self.identifier(spec) == target:
                raise SourceError("Source schema no longer matches this candidate")
            return self.captured_primary(client, spec)
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary) as singstat, \
                patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct) as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series") as mas:
            result = run_workflow("2026-10-01", output, progress=lambda _: None)
        self.assertEqual([self.identifier(call.args[1]) for call in singstat.call_args_list], self.catalogue_ids(output))
        mom.assert_called_once()
        self.assertEqual(self.identifier(mom.call_args.args[1]), target)
        mas.assert_not_called()
        routes = self.routes(output)
        self.assertEqual(routes[target]["used_source"], "MOM")
        self.assertEqual([(a["stage"], a["status"]) for a in routes[target]["attempts"]],
                         [("primary", "failed"), ("fallback", "ok")])
        self.assertFalse(routes[target]["attempts"][0]["retryable"])
        self.assertTrue(all(route["used_source"] == "SingStat" for key, route in routes.items() if key != target))
        self.assertEqual(result["source_coverage"]["singstat_downloaded"], len(routes) - 1)
        self.assertEqual(result["source_coverage"]["fallback_downloaded"], 1)
        normalized = {series["id"]: series for series in read_json(output / "normalized.json")}
        self.assertEqual(normalized[target]["source_provider"], "Synthetic MOM fixture")

    def test_fallback_waits_until_primary_recheck_has_failed(self):
        target = "M700071:23"
        output = self.root / "recheck-fallback"
        order = []
        def primary(client, spec):
            identifier = self.identifier(spec)
            order.append(("SingStat", identifier))
            if identifier == target:
                raise SourceUnavailableError("Repeated temporary gateway failure")
            return self.captured_primary(client, spec)
        def fallback(client, spec, *args):
            order.append(("MAS", self.identifier(spec)))
            return self.captured_direct(client, spec, *args)
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series", side_effect=fallback) as mas:
            run_workflow("2026-10-01", output, progress=lambda _: None)
        self.assertEqual(order, [("SingStat", key) for key in self.catalogue_ids(output)] + [("SingStat", target), ("MAS", target)])
        mom.assert_not_called()
        mas.assert_called_once()
        route = self.routes(output)[target]
        self.assertEqual(route["used_source"], "MAS")
        self.assertEqual([(a["stage"], a["status"]) for a in route["attempts"]],
                         [("primary", "failed"), ("primary_recheck", "failed"), ("fallback", "ok")])
        self.assertTrue(all(a["retryable"] for a in route["attempts"][:2]))

    def test_singstat_policy_isolates_failed_candidates_and_never_uses_fallback(self):
        transient, permanent = "M182342:2", "M700071:23"
        output = self.root / "singstat-only"
        calls = []
        def primary(client, spec):
            identifier = self.identifier(spec)
            calls.append(identifier)
            if identifier == transient:
                raise SourceMaintenanceError("Maintenance for this candidate")
            if identifier == permanent:
                raise SourceError("Invalid source schema")
            return self.captured_primary(client, spec)
        with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=SourceUnavailableError("Search unavailable")), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series") as mas:
            result = run_workflow("2026-10-01", output, source_policy="singstat", progress=lambda _: None)
        self.assertEqual(calls, self.catalogue_ids(output) + [transient])
        mom.assert_not_called()
        mas.assert_not_called()
        routes = self.routes(output)
        self.assertEqual(routes[transient]["status"], "failed")
        self.assertEqual(routes[permanent]["status"], "failed")
        self.assertIsNone(routes[transient]["used_source"])
        self.assertIsNone(routes[permanent]["used_source"])
        self.assertFalse({transient, permanent} & set(result["selected_ids"]))
        self.assertEqual(result["source_coverage"]["singstat_downloaded"], len(routes) - 2)
        self.assertEqual(result["source_coverage"]["fallback_downloaded"], 0)
        self.assert_candidate_coverage(output)

    def test_mixed_source_snapshot_and_replay_preserve_actual_sources_offline(self):
        output = self.root / "mixed"
        def primary(client, spec):
            if self.identifier(spec) in DIRECT_IDS:
                raise SourceError("Permanent primary schema failure")
            return self.captured_primary(client, spec)
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct), \
                patch("housing_agent.mas_sources.fetch_mas_series", side_effect=self.captured_direct):
            result = run_workflow("2026-10-01", output, progress=lambda _: None)
        self.assertEqual(result["source_coverage"]["fallback_downloaded"], len(DIRECT_IDS))
        self.assertEqual(result["source_coverage"]["singstat_downloaded"], len(self.catalogue_ids(output)) - len(DIRECT_IDS))
        source_bytes = {str(path.relative_to(output)): path.read_bytes() for path in output.rglob("*") if path.is_file()}
        replayed = self.root / "replay.md"
        replay(output, replayed)
        self.assertEqual(replayed.read_bytes(), (output / "report.md").read_bytes())
        with patch("housing_agent.pipeline.SingStatClient", side_effect=AssertionError("Saved source must stay offline")), \
                patch("housing_agent.pipeline.OfficialFileClient", side_effect=AssertionError("Saved source must stay offline")), \
                patch("housing_agent.pipeline.fetch_series", side_effect=AssertionError("No source refresh")), \
                patch("housing_agent.mom_sources.fetch_mom_series", side_effect=AssertionError("No source refresh")), \
                patch("housing_agent.mas_sources.fetch_mas_series", side_effect=AssertionError("No source refresh")):
            saved = run_workflow("2026-10-01", self.root / "saved", source_run=output, progress=lambda _: None)
        self.assertEqual(set(saved["selected_ids"]), set(result["selected_ids"]))
        self.assertEqual(saved["source_policy"], "saved")
        self.assertEqual(read_json(self.root / "saved/normalized.json"), read_json(output / "normalized.json"))
        self.assertEqual(source_bytes, {str(path.relative_to(output)): path.read_bytes() for path in output.rglob("*") if path.is_file()})

    def test_failed_fallback_preserves_other_primary_and_fallback_results(self):
        output = self.root / "partial-backup"
        def primary(client, spec):
            if self.identifier(spec) in DIRECT_IDS:
                raise SourceError("Primary schema mismatch")
            return self.captured_primary(client, spec)
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct) as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series", side_effect=SourceError("MAS form changed")) as mas:
            result = run_workflow("2026-10-01", output, progress=lambda _: None)
        ids = self.catalogue_ids(output)
        self.assertEqual(mom.call_count, len(DIRECT_IDS - {"M700071:23"}))
        mas.assert_called_once()
        self.assertEqual(result["source_coverage"]["downloaded"], len(ids) - 1)
        self.assertNotIn("M700071:23", result["selected_ids"])
        route = self.routes(output)["M700071:23"]
        self.assertEqual(route["status"], "failed")
        self.assertIsNone(route["used_source"])
        self.assertIn("MAS form changed", route["attempts"][-1]["error"])
        self.assertIn("MAS form changed", (output / "report.md").read_text())
        self.assert_candidate_coverage(output)

    def test_no_source_available_finishes_two_primary_rounds_and_fallback_before_rejecting_model(self):
        output = self.root / "failed"
        order = []
        def primary(client, spec):
            order.append(("SingStat", self.identifier(spec)))
            raise SourceUnavailableError("Temporary primary failure")
        def fallback(client, spec, *args):
            order.append(("fallback", self.identifier(spec)))
            raise SourceError("Independent source unavailable")
        with patch.dict(os.environ, {"SOCLAAS_API_KEY": "synthetic-test-key", "SOCLAAS_MODEL": "synthetic-test-model"}), \
                patch("housing_agent.pipeline.SingStatClient.discover", side_effect=SourceMaintenanceError("Search endpoint maintenance")), \
                patch("housing_agent.pipeline.fetch_series", side_effect=primary), \
                patch("housing_agent.mom_sources.fetch_mom_series", side_effect=fallback), \
                patch("housing_agent.mas_sources.fetch_mas_series", side_effect=fallback), \
                patch("housing_agent.agent.run_agent") as agent:
            with self.assertRaisesRegex(ValueError, "No candidate"):
                run_workflow("2026-10-01", output, mode="llm", provider="soclaas", progress=lambda _: None)
        ids = self.catalogue_ids(output)
        self.assertEqual(order[:2 * len(ids)], [("SingStat", key) for key in ids] * 2)
        self.assertEqual(Counter(order[2 * len(ids):]), Counter(("fallback", key) for key in ids if key in DIRECT_IDS))
        agent.assert_not_called()
        self.assert_candidate_coverage(output)
        self.assertFalse((output / "report.md").exists())
        manifest = read_json(output / "manifest.json")
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["usage"]["requests"], 0)
        self.assertIn("source_routes.json", manifest["files"])
        for identifier, route in self.routes(output).items():
            self.assertEqual(route["status"], "failed")
            self.assertIsNone(route["used_source"])
            expected = ["primary", "primary_recheck"] + (["fallback"] if identifier in DIRECT_IDS else [])
            self.assertEqual([a["stage"] for a in route["attempts"]], expected)

    def test_unknown_source_policy_fails_before_creating_output(self):
        output = self.root / "bad"
        with patch("housing_agent.pipeline.fetch_series") as primary, \
                patch("housing_agent.mom_sources.fetch_mom_series") as mom, \
                patch("housing_agent.mas_sources.fetch_mas_series") as mas:
            with self.assertRaisesRegex(ValueError, "source policy"):
                run_workflow("2026-10-01", output, source_policy="unknown", progress=lambda _: None)
        primary.assert_not_called()
        mom.assert_not_called()
        mas.assert_not_called()
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
