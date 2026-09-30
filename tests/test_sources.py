"""Source regressions against unmodified official captures; no network is used."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from housing_agent.sources import SingStatClient, SourceError, fetch_series

FIXTURES = Path(__file__).parent / "fixtures"
CATALOGUE = Path(__file__).parents[1] / "housing_agent" / "data" / "catalogue.json"


def captured(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Response(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.headers = {"Content-Type": "application/json"}


class CapturedSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.client = SingStatClient(self.root)
        self.catalogue = {(item["table_id"], item["row_id"]): item
                          for item in json.loads(CATALOGUE.read_text(encoding="utf-8"))}
        self.requests = []

    def spec(self, table="M015661", row="1"):
        return deepcopy(self.catalogue[table, row])

    def response_source(self, replacements=None):
        """Serve exact original bytes, except explicit adversarial mutations."""
        replacements = replacements or {}

        def open_captured(request, timeout):
            self.requests.append(request)
            parsed = urlparse(request.full_url)
            kind, table = parsed.path.split("/")[-2:]
            if kind == "metadata":
                self.assertEqual(parsed.query, "")
                filename = f"metadata_{table}.json"
            else:
                self.assertEqual(kind, "tabledata")
                query = parse_qs(parsed.query)
                # Whole-table downloads silently cap cells, even mid-series.
                self.assertEqual(set(query), {"seriesNoORrowNo", "limit"})
                self.assertEqual(query["limit"], ["5000"])
                self.assertEqual(len(query["seriesNoORrowNo"]), 1)
                filename = f"tabledata_{table}_{query['seriesNoORrowNo'][0]}.json"
            body = (json.dumps(replacements[filename]).encode()
                    if filename in replacements else (FIXTURES / filename).read_bytes())
            return Response(body)
        return patch("housing_agent.sources.urlopen", side_effect=open_captured)

    def test_real_gdp_quarters_normalize_without_discarding_observations(self):
        # Original regression rejected all official labels of form YYYY nQ.
        with self.response_source():
            series = fetch_series(self.client, self.spec())
        self.assertEqual(len(series["observations"]), 206)
        self.assertEqual(series["observations"][0]["period"], "1975-Q1")
        latest = series["observations"][-1]
        self.assertEqual(latest["period"], "2026-Q2")
        self.assertEqual(latest["raw_period"], "2026 2Q")
        self.assertEqual(latest["value"], 155247.2)
        self.assertEqual(latest["raw_value"], "155247.2")
        self.assertEqual(latest["raw_index"], 205)
        self.assertEqual(series["source_url"], "https://tablebuilder.singstat.gov.sg/table/TS/M015661")
        self.assertEqual(series["comparisons"], ["year_on_year"])

    def test_population_reference_override_is_supported_by_actual_source_note(self):
        with self.response_source():
            series = fetch_series(self.client, self.spec("M810001", "2"))
        self.assertIn("Data are as at end-June", series["row_footnote"])
        self.assertEqual(len(series["observations"]), 48)
        self.assertEqual(series["source_updated_at"], "25/09/2026")
        latest = series["observations"][-1]
        self.assertEqual(latest["period"], "2026")
        self.assertEqual(latest["value"], 4231524)
        self.assertEqual(latest["observation_date"], "2026-06-30")
        self.assertTrue(all(row["observation_date"] == row["period"] + "-06-30"
                            for row in series["observations"]))
        # Current table update is not first publication of every historical row.
        self.assertTrue(all("published_at" not in row for row in series["observations"]))

    def test_real_monthly_sora_keys_and_month_end_definition_are_preserved(self):
        with self.response_source():
            series = fetch_series(self.client, self.spec("M700071", "23"))
        self.assertEqual(len(series["observations"]), 251)
        self.assertEqual(series["observations"][0]["period"], "2005-10")
        self.assertEqual(series["observations"][-1]["period"], "2026-08")
        self.assertEqual(series["observations"][-1]["raw_period"], "2026 Aug")
        self.assertEqual(series["observations"][-1]["value"], 1.1863)
        self.assertIn("end of month", series["source_footnote"])
        self.assertEqual(series["unit"], "Per Cent Per Annum")
        self.assertEqual(series["change_kind"], "basis_point")

    def test_metadata_and_exact_row_requests_are_audited_and_cached(self):
        with self.response_source() as opening:
            first = fetch_series(self.client, self.spec())
            second = fetch_series(self.client, self.spec())
        self.assertEqual(opening.call_count, 2)
        self.assertEqual(first, second)
        self.assertIn("/metadata/M015661", self.requests[0].full_url)
        self.assertEqual(parse_qs(urlparse(self.requests[1].full_url).query),
                         {"seriesNoORrowNo": ["1"], "limit": ["5000"]})
        self.assertTrue(all(r.get_header("User-agent") for r in self.requests))
        self.assertTrue(all(r.get_header("Accept") == "application/json" for r in self.requests))
        provenance = first["provenance"]
        for field, filename in [("raw", "tabledata_M015661_1.json"),
                                ("metadata", "metadata_M015661.json")]:
            saved = self.root / provenance[field + "_file"]
            self.assertEqual(saved.read_bytes(), (FIXTURES / filename).read_bytes())
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), provenance[field + "_sha256"])
        self.client.save_records()
        records = json.loads((self.root / "retrievals.json").read_text())
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record["status"] == "ok" for record in records))
        self.assertTrue(all(record["retrieved_at"] for record in records))

    def test_captured_live_metadata_matches_catalogue_and_exact_data(self):
        for table, row in [("M015661", "1"), ("M810001", "2"), ("M700071", "23")]:
            with self.subTest(table=table, row=row):
                meta = captured(f"metadata_{table}.json")["Data"]["records"]
                data = captured(f"tabledata_{table}_{row}.json")["Data"]
                self.assertIsInstance(meta, dict)
                rows = [r for r in meta["row"] if r["seriesNo"] == row]
                self.assertEqual(len(rows), 1)
                spec = self.spec(table, row)
                self.assertEqual(meta["id"], table)
                self.assertEqual(data["id"], table)
                self.assertEqual(meta["frequency"], data["frequency"])
                self.assertEqual(rows[0]["rowText"], spec["expected_name"])
                self.assertEqual(rows[0]["uoM"], spec["expected_unit"])
                self.assertEqual(data["row"][0]["rowText"], rows[0]["rowText"])
                self.assertEqual(data["row"][0]["uoM"], rows[0]["uoM"])

    def test_drift_in_live_name_unit_or_frequency_is_rejected(self):
        for field, value in [("rowText", "GDP after a definition revision"),
                             ("uoM", "Billion Dollars"), ("frequency", "Monthly")]:
            with self.subTest(field=field):
                data = captured("tabledata_M015661_1.json")
                if field == "frequency":
                    data["Data"][field] = value
                else:
                    data["Data"]["row"][0][field] = value
                with self.response_source({"tabledata_M015661_1.json": data}):
                    with self.assertRaises(SourceError):
                        fetch_series(SingStatClient(self.root / field), self.spec())

    def test_metadata_and_data_must_agree_before_publishing_audit_evidence(self):
        for field, value in [("rowText", "Revised GDP concept"),
                             ("uoM", "Billion Dollars"), ("frequency", "Monthly"),
                             ("id", "M810001")]:
            with self.subTest(field=field):
                metadata = captured("metadata_M015661.json")
                meta = metadata["Data"]["records"]
                if field in {"rowText", "uoM"}:
                    next(row for row in meta["row"] if row["seriesNo"] == "1")[field] = value
                else:
                    meta[field] = value
                with self.response_source({"metadata_M015661.json": metadata}):
                    with self.assertRaises(SourceError):
                        fetch_series(SingStatClient(self.root / field), self.spec())

    def test_response_table_identity_cannot_silently_change(self):
        data = captured("tabledata_M015661_1.json")
        data["Data"]["id"] = "M810001"
        with self.response_source({"tabledata_M015661_1.json": data}):
            with self.assertRaises(SourceError):
                fetch_series(self.client, self.spec())

    def test_ambiguous_or_absent_row_is_rejected(self):
        for duplicate in [False, True]:
            data = captured("tabledata_M015661_1.json")
            data["Data"]["row"] = data["Data"]["row"] * 2 if duplicate else []
            with self.subTest(duplicate=duplicate):
                with self.response_source({"tabledata_M015661_1.json": data}):
                    with self.assertRaises(SourceError):
                        fetch_series(SingStatClient(self.root / str(duplicate)), self.spec())

    def test_exact_cell_cap_is_rejected_as_possible_truncation(self):
        data = captured("tabledata_M015661_1.json")
        column = data["Data"]["row"][0]["columns"][0]
        data["Data"]["row"][0]["columns"] = [deepcopy(column) for _ in range(5000)]
        with self.response_source({"tabledata_M015661_1.json": data}):
            with self.assertRaisesRegex(SourceError, "truncat|pagination"):
                fetch_series(self.client, self.spec())

    def test_checked_in_capture_provenance_matches_original_bytes(self):
        manifest = captured("provenance.json")
        self.assertEqual(len(manifest["records"]), 6)
        for record in manifest["records"]:
            with self.subTest(file=record["file"]):
                self.assertEqual(hashlib.sha256((FIXTURES / record["file"]).read_bytes()).hexdigest(), record["sha256"])
                self.assertEqual(urlparse(record["url"]).hostname, "tablebuilder.singstat.gov.sg")
                self.assertEqual(record["http_status"], 200)
                self.assertEqual(record["api_status"], 200)
                self.assertTrue(record["retrieved_at"])


class TransportFailureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_api_failure_inside_http_success_is_failed_and_not_cached(self):
        body = json.dumps({"Data": {"records": []}, "StatusCode": 400,
                           "Message": "Invalid resource"}).encode()
        client = SingStatClient(self.root, retries=2)
        with patch("housing_agent.sources.urlopen", return_value=Response(body)) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceError):
                    client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 1)
        sleeping.assert_not_called()
        self.assertFalse(client.cache)
        self.assertEqual(client.records[0]["status"], "failed")
        self.assertEqual(len(client.records[0]["attempts"]), 1)

    def test_temporary_http_failure_has_finite_retries_and_a_failure_record(self):
        error = HTTPError("https://tablebuilder.singstat.gov.sg/api/table/metadata/M015661", 503, "Service Unavailable", {}, None)
        client = SingStatClient(self.root, retries=2)
        with patch("housing_agent.sources.urlopen", side_effect=error) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceError):
                    client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 3)
        self.assertEqual(sleeping.call_count, 2)
        client.save_records()
        record = json.loads((self.root / "retrievals.json").read_text())[0]
        self.assertEqual(record["status"], "failed")
        self.assertEqual([a["status"] for a in record["attempts"]], ["failed"] * 3)
        self.assertIn("503", record["error"])
        self.assertFalse(client.cache)

    def test_permanent_http_failure_is_not_blindly_retried(self):
        error = HTTPError("https://tablebuilder.singstat.gov.sg/api/table/metadata/M015661", 404, "Not Found", {}, None)
        client = SingStatClient(self.root, retries=2)
        with patch("housing_agent.sources.urlopen", side_effect=error) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceError):
                    client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 1)
        sleeping.assert_not_called()
        self.assertEqual(client.records[0]["status"], "failed")

    def test_recovery_preserves_failed_attempt_and_original_success_bytes(self):
        body = (FIXTURES / "metadata_M015661.json").read_bytes()
        client = SingStatClient(self.root, retries=1)
        with patch("housing_agent.sources.urlopen", side_effect=[URLError("temporary DNS failure"), Response(body)]) as opening:
            with patch("housing_agent.sources.time.sleep"):
                payload, record = client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 2)
        self.assertEqual(payload["Data"]["records"]["id"], "M015661")
        self.assertEqual(record["status"], "ok")
        self.assertEqual([item["status"] for item in record["attempts"]], ["failed", "ok"])
        self.assertEqual((self.root / record["raw_file"]).read_bytes(), body)
        self.assertEqual(record["raw_sha256"], hashlib.sha256(body).hexdigest())


if __name__ == "__main__":
    unittest.main()
