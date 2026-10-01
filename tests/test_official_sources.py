"""Transport boundaries and mixed-source failure isolation; no live requests."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from housing_agent.official_sources import OfficialFileClient, SourceError, _OfficialRedirects
from housing_agent.pipeline import run_workflow, replay
from housing_agent.sources import SourceMaintenanceError
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
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        loader = patch("housing_agent.pipeline.load_local_environment")
        loader.start()
        self.addCleanup(loader.stop)

    def captured_direct(self, client, spec, *args):
        series = specimen(spec)
        token = spec["table_id"]
        raw = client.run_dir / "raw" / f"{token}.csv"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"synthetic test observations\n")
        metadata = client.metadata(token, {"note": "Synthetic fixture, not official data"})
        record = {"url": "https://stats.mom.gov.sg/fixture.csv", "retrieved_at": series["retrieved_at"],
                  "status": "ok", "attempts": [{"status": "ok"}], "raw_file": str(raw.relative_to(client.run_dir)),
                  "raw_sha256": sha256_bytes(raw.read_bytes())}
        client.records.append(record)
        series["source_provider"] = "Synthetic independent official source fixture"
        series["provenance"] = {"raw_file": record["raw_file"], "raw_sha256": record["raw_sha256"],
                                "metadata_file": metadata["raw_file"], "metadata_sha256": metadata["raw_sha256"]}
        for observation in series["observations"]:
            observation["raw_locator"] = "CSV row 2"
        return series

    def test_maintenance_does_not_block_direct_sources_and_snapshot_replay(self):
        output = self.root / "mixed"
        with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=SourceMaintenanceError("official maintenance")) as discover, patch("housing_agent.pipeline.fetch_series") as singstat, patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct) as mom, patch("housing_agent.mas_sources.fetch_mas_series", side_effect=self.captured_direct) as mas:
            result = run_workflow("2026-10-01", output, progress=lambda _: None)
        self.assertEqual(discover.call_count, 1)
        singstat.assert_not_called()
        self.assertEqual(mom.call_count, 2)
        self.assertEqual(mas.call_count, 1)
        self.assertEqual(set(result["selected_ids"]), {"M182342:2", "M184101:1", "M700071:23"})
        self.assertEqual(result["source_policy"], "auto")
        self.assertEqual(result["source_coverage"]["downloaded"], 3)
        self.assertEqual(len(read_json(output / "evaluations.json")), 12)
        self.assertEqual(result["usage"]["total_tokens"], 0)
        report = (output / "report.md").read_text()
        self.assertIn("Synthetic independent official source fixture", report)
        self.assertNotIn("via [SingStat Table Builder]", report)
        replay(output, self.root / "replay.md")
        # Saved data from every format must remain usable without any HTTP client.
        with patch("housing_agent.pipeline.SingStatClient", side_effect=AssertionError("Offline")), patch("housing_agent.pipeline.OfficialFileClient", side_effect=AssertionError("Offline")):
            saved = run_workflow("2026-10-01", self.root / "saved", source_run=output, progress=lambda _: None)
        self.assertEqual(set(saved["selected_ids"]), set(result["selected_ids"]))
        self.assertEqual(saved["source_policy"], "saved")

    def test_one_independent_failure_preserves_other_sources(self):
        with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=SourceMaintenanceError("maintenance")), patch("housing_agent.pipeline.fetch_series") as singstat, patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct), patch("housing_agent.mas_sources.fetch_mas_series", side_effect=SourceError("MAS form changed")):
            result = run_workflow("2026-10-01", self.root / "partial", progress=lambda _: None)
        singstat.assert_not_called()
        self.assertEqual(set(result["selected_ids"]), {"M182342:2", "M184101:1"})
        self.assertIn("MAS form changed", (self.root / "partial/report.md").read_text())

    def test_maintenance_first_seen_during_series_fetch_still_allows_direct_routes(self):
        with patch("housing_agent.pipeline.SingStatClient.discover", return_value=[]), patch("housing_agent.pipeline.fetch_series", side_effect=SourceMaintenanceError("maintenance after discovery")) as singstat, patch("housing_agent.mom_sources.fetch_mom_series", side_effect=self.captured_direct), patch("housing_agent.mas_sources.fetch_mas_series", side_effect=self.captured_direct):
            result = run_workflow("2026-10-01", self.root / "late-maintenance", progress=lambda _: None)
        self.assertEqual(singstat.call_count, 1)
        self.assertEqual(len(result["selected_ids"]), 3)
        self.assertTrue(result["source_coverage"]["singstat_maintenance"])

    def test_no_source_available_does_not_call_model_or_create_report(self):
        output = self.root / "failed"
        with patch("housing_agent.pipeline.SingStatClient.discover", side_effect=SourceMaintenanceError("maintenance")), patch("housing_agent.mom_sources.fetch_mom_series", side_effect=SourceError("MOM unavailable")), patch("housing_agent.mas_sources.fetch_mas_series", side_effect=SourceError("MAS unavailable")), patch("housing_agent.agent.run_agent") as agent:
            with self.assertRaisesRegex(ValueError, "No candidate"):
                run_workflow("2026-10-01", output, progress=lambda _: None)
        agent.assert_not_called()
        self.assertFalse((output / "report.md").exists())
        self.assertEqual(read_json(output / "manifest.json")["status"], "failed")

    def test_unknown_source_policy_fails_before_creating_output(self):
        output = self.root / "bad"
        with self.assertRaisesRegex(ValueError, "source policy"):
            run_workflow("2026-10-01", output, source_policy="unknown", progress=lambda _: None)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
