"""Source regressions against unmodified official captures; no network is used."""
from copy import deepcopy
from http.client import HTTPException, IncompleteRead
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from housing_agent.sources import SingStatClient, SourceError, SourceMaintenanceError, SourceUnavailableError, fetch_series

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

    def test_incomplete_response_retries_then_preserves_both_partial_and_success(self):
        partial = b'{"StatusCode": 200, "Data": '
        class InterruptedResponse(Response):
            def read(self, size=-1):
                raise IncompleteRead(partial, 100)
        body = (FIXTURES / "metadata_M015661.json").read_bytes()
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", side_effect=[InterruptedResponse(b""), Response(body)]) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                payload, record = client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 2)
        sleeping.assert_called_once_with(1)
        self.assertEqual(payload["Data"]["records"]["id"], "M015661")
        self.assertEqual(record["status"], "ok")
        self.assertEqual([item["status"] for item in record["attempts"]], ["failed", "ok"])
        failed = record["attempts"][0]
        self.assertEqual(failed["http_status"], 200)
        self.assertTrue(failed["error_body_incomplete"])
        self.assertEqual((self.root / failed["error_body_prefix_file"]).read_bytes(), partial)
        self.assertEqual(failed["error_body_prefix_sha256"], hashlib.sha256(partial).hexdigest())
        self.assertEqual((self.root / record["raw_file"]).read_bytes(), body)

    def test_persistent_incomplete_response_is_temporary_and_all_attempts_audited(self):
        partial = b'{"Data": "' + b"x" * 20000
        class InterruptedResponse(Response):
            def read(self, size=-1):
                raise IncompleteRead(partial, 100)
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", side_effect=lambda *a, **k: InterruptedResponse(b"")) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceUnavailableError) as raised:
                    client.get("metadata/M015661")
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(opening.call_count, 3)
        self.assertEqual([call.args[0] for call in sleeping.call_args_list], [1, 2])
        self.assertFalse(client.cache)
        record = client.records[0]
        self.assertEqual(record["status"], "failed")
        self.assertTrue(record["completed_at"])
        self.assertEqual(len(record["attempts"]), 3)
        paths = set()
        for attempt in record["attempts"]:
            self.assertEqual(attempt["status"], "failed")
            self.assertIn("IncompleteRead", attempt["error"])
            self.assertTrue(attempt["error_body_incomplete"])
            self.assertTrue(attempt["error_body_prefix_truncated"])
            self.assertTrue(attempt["retrieved_at"])
            self.assertTrue(attempt["completed_at"])
            path = self.root / attempt["error_body_prefix_file"]
            self.assertEqual(path.read_bytes(), partial[:16 * 1024])
            self.assertEqual(attempt["error_body_prefix_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            paths.add(path)
        self.assertEqual(len(paths), 3)

    def test_other_http_protocol_error_is_temporary_without_invented_partial_body(self):
        client = SingStatClient(self.root)
        error = HTTPException("Invalid HTTP response")
        error.partial = 100  # Only actual received bytes may be saved as evidence.
        with patch("housing_agent.sources.urlopen", side_effect=error) as opening:
            with patch("housing_agent.sources.time.sleep"):
                with self.assertRaises(SourceUnavailableError):
                    client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 3)
        self.assertEqual(client.records[0]["status"], "failed")
        self.assertEqual(len(client.records[0]["attempts"]), 3)
        self.assertTrue(all("error_body_prefix_file" not in item for item in client.records[0]["attempts"]))

    def test_incomplete_http_error_body_preserves_status_and_permanent_error_policy(self):
        partial = b"<html><body>Not Found"
        class InterruptedBody(io.BytesIO):
            def read(self, size=-1):
                raise IncompleteRead(partial, 100)
        for status, attempts, error_type in ((404, 1, SourceError), (502, 3, SourceUnavailableError)):
            with self.subTest(status=status):
                def fail(*args, **kwargs):
                    raise HTTPError("https://tablebuilder.singstat.gov.sg/api/table/metadata/M015661", status,
                                    "Incomplete error page", {"Content-Type": "text/html"}, InterruptedBody())
                client = SingStatClient(self.root / str(status))
                with patch("housing_agent.sources.urlopen", side_effect=fail) as opening:
                    with patch("housing_agent.sources.time.sleep"):
                        with self.assertRaises(error_type) as raised:
                            client.get("metadata/M015661")
                self.assertEqual(raised.exception.retryable, status == 502)
                self.assertEqual(opening.call_count, attempts)
                self.assertEqual(client.records[0]["status"], "failed")
                for attempt in client.records[0]["attempts"]:
                    self.assertEqual(attempt["http_status"], status)
                    self.assertTrue(attempt["error_body_incomplete"])
                    self.assertIn("IncompleteRead", attempt["error_body_read_error"])
                    self.assertEqual((client.run_dir / attempt["error_body_prefix_file"]).read_bytes(), partial)


# Actual notice excerpt returned by the official SingStat maintenance page in
# the transport diagnostic. It is source text only; no HTML is executed.
MAINTENANCE_HTML = b"""<!DOCTYPE html><html><head><title>Statistics Singapore</title></head>
<body><h2>The SingStat Table Builder and SANDRA  (Statistics ANd Data Retrieval A.I. assistant)
are currently undergoing maintenance. </h2>
<h2>We will work to complete the maintenance work ASAP.</h2>
<h2>Thank you for your patience.</h2></body></html>"""


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def error(self, body, status=502):
        return HTTPError("https://tablebuilder.singstat.gov.sg/api/table/metadata/M015661",
                         status, "Bad Gateway", {"Content-Type": "text/html", "Retry-After": "120",
                         "Date": "Thu, 01 Oct 2026 01:00:00 GMT", "Cache-Control": "no-cache", "Age": "15",
                         "Server": "Microsoft-Azure-Application-Gateway/v2", "Set-Cookie": "never-persist"}, io.BytesIO(body))

    def test_repeated_notice_retries_and_keeps_each_original_failure_prefix(self):
        client = SingStatClient(self.root)
        def fail(*args, **kwargs):
            raise self.error(MAINTENANCE_HTML)
        with patch("housing_agent.sources.urlopen", side_effect=fail) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaisesRegex(SourceMaintenanceError, "Request exhausted its retries") as raised:
                    client.get("metadata/M015661")
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(opening.call_count, 3)
        self.assertEqual([call.args[0] for call in sleeping.call_args_list], [1, 2])
        self.assertFalse(client.cache)
        client.save_records()
        record = json.loads((self.root / "retrievals.json").read_text())[0]
        self.assertEqual(record["http_status"], 502)
        self.assertEqual(record["response_headers"], {"server": "Microsoft-Azure-Application-Gateway/v2",
                         "content-type": "text/html", "retry-after": "120", "age": "15",
                         "date": "Thu, 01 Oct 2026 01:00:00 GMT", "cache-control": "no-cache"})
        self.assertEqual(record["status"], "failed")
        self.assertTrue(record["maintenance"])
        self.assertEqual(len(record["attempts"]), 3)
        files = set()
        for attempt in record["attempts"]:
            self.assertEqual(attempt["http_status"], 502)
            self.assertIn("SANDRA", attempt["maintenance_notice"])
            self.assertNotIn("<h2>", attempt["maintenance_notice"])
            self.assertTrue(attempt["retrieved_at"])
            self.assertTrue(attempt["completed_at"])
            path = self.root / attempt["error_body_prefix_file"]
            self.assertEqual(path.read_bytes(), MAINTENANCE_HTML)
            self.assertEqual(attempt["error_body_prefix_sha256"], hashlib.sha256(MAINTENANCE_HTML).hexdigest())
            self.assertEqual(attempt["error_body_prefix_bytes"], len(MAINTENANCE_HTML))
            self.assertFalse(attempt["error_body_prefix_truncated"])
            files.add(path)
        self.assertEqual(len(files), 3)
        self.assertNotIn("never-persist", json.dumps(record))
        self.assertEqual(record["maintenance_source_url"], record["url"])

    def test_maintenance_then_success_preserves_failure_but_clears_current_status(self):
        body = (FIXTURES / "metadata_M015661.json").read_bytes()
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", side_effect=[self.error(MAINTENANCE_HTML), Response(body)]) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                payload, record = client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 2)
        sleeping.assert_called_once_with(1)
        self.assertEqual(payload["Data"]["records"]["id"], "M015661")
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["http_status"], 200)
        self.assertNotIn("maintenance", record)
        self.assertNotIn("maintenance_notice", record)
        self.assertIn("maintenance_notice", record["attempts"][0])
        self.assertIsNone(client.maintenance)
        self.assertEqual((self.root / record["raw_file"]).read_bytes(), body)

    def test_new_endpoint_is_attempted_after_exhausted_maintenance(self):
        body = (FIXTURES / "metadata_M810001.json").read_bytes()
        client = SingStatClient(self.root)
        sequence = [self.error(MAINTENANCE_HTML) for _ in range(3)] + [Response(body)]
        with patch("housing_agent.sources.urlopen", side_effect=sequence) as opening:
            with patch("housing_agent.sources.time.sleep"):
                with self.assertRaises(SourceMaintenanceError):
                    client.get("metadata/M015661")
                payload, record = client.get("metadata/M810001")
        self.assertEqual(opening.call_count, 4)
        self.assertEqual(payload["Data"]["records"]["id"], "M810001")
        self.assertEqual(len(client.records), 2)
        self.assertEqual(record["status"], "ok")
        self.assertTrue(record["url"].endswith("/metadata/M810001"))
        self.assertIsNone(client.maintenance)

    def test_same_failed_endpoint_can_be_rechecked_without_refresh_option(self):
        body = (FIXTURES / "metadata_M015661.json").read_bytes()
        client = SingStatClient(self.root)
        sequence = [self.error(MAINTENANCE_HTML) for _ in range(3)] + [Response(body)]
        with patch("housing_agent.sources.urlopen", side_effect=sequence) as opening:
            with patch("housing_agent.sources.time.sleep"):
                with self.assertRaises(SourceMaintenanceError):
                    client.get("metadata/M015661")
                _, record = client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 4)
        self.assertEqual(record["status"], "ok")
        self.assertIsNone(client.maintenance)
        self.assertEqual(len(client.records), 2)

    def test_http_200_maintenance_also_receives_bounded_retries(self):
        def response(*args, **kwargs):
            item = Response(MAINTENANCE_HTML)
            item.headers = {"Content-Type": "text/html"}
            return item
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", side_effect=response) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceMaintenanceError):
                    client.get("metadata/M015661")
        self.assertEqual(opening.call_count, 3)
        self.assertEqual(sleeping.call_count, 2)
        self.assertEqual(client.records[0]["http_status"], 200)
        self.assertFalse(client.cache)

    def test_generic_502_is_temporary_not_maintenance_and_keeps_bounded_retries(self):
        client = SingStatClient(self.root)
        def fail(*args, **kwargs):
            raise self.error(b"<html><h1>Bad Gateway</h1></html>")
        with patch("housing_agent.sources.urlopen", side_effect=fail) as opening:
            with patch("housing_agent.sources.time.sleep") as sleeping:
                with self.assertRaises(SourceUnavailableError) as raised:
                    client.get("metadata/M015661")
        self.assertTrue(raised.exception.retryable)
        self.assertNotIsInstance(raised.exception, SourceMaintenanceError)
        self.assertEqual(opening.call_count, 3)
        self.assertEqual(sleeping.call_count, 2)
        self.assertEqual(len(client.records[0]["attempts"]), 3)
        self.assertIsNone(client.maintenance)
        self.assertTrue(all(item["error_body_prefix_file"] for item in client.records[0]["attempts"]))

    def test_final_generic_failure_does_not_retain_earlier_maintenance_diagnosis(self):
        client = SingStatClient(self.root)
        sequence = [self.error(MAINTENANCE_HTML), self.error(b"Bad Gateway"), self.error(b"Bad Gateway")]
        with patch("housing_agent.sources.urlopen", side_effect=sequence), patch("housing_agent.sources.time.sleep"):
            with self.assertRaises(SourceUnavailableError):
                client.get("metadata/M015661")
        self.assertIsNone(client.maintenance)
        self.assertNotIn("maintenance_notice", client.records[0])
        self.assertIn("maintenance_notice", client.records[0]["attempts"][0])

    def test_historical_future_quoted_and_script_notices_are_not_current_status(self):
        bodies = [b"<html>SingStat Table Builder: unexpected upstream response</html>",
                  b'<html><script>var message="SingStat Table Builder is currently undergoing maintenance";</script>Malformed</html>',
                  b'<html><body>News archive: The SingStat Table Builder is currently undergoing maintenance.</body></html>',
                  b'<html><body>The SingStat Table Builder was undergoing maintenance.</body></html>',
                  b'<html><body>The SingStat Table Builder will be undergoing maintenance.</body></html>',
                  b'<html><body>The SingStat Table Builder is not currently undergoing maintenance.</body></html>',
                  b'<html><body><time>2025-01-01</time>The SingStat Table Builder is currently undergoing maintenance.</body></html>',
                  b'<html><body><!-- The SingStat Table Builder is currently undergoing maintenance. -->Malformed</body></html>']
        for body in bodies:
            with self.subTest(body=body):
                client = SingStatClient(self.root)
                with patch("housing_agent.sources.urlopen", return_value=Response(body)) as opening:
                    with patch("housing_agent.sources.time.sleep") as sleeping:
                        with self.assertRaises(SourceError) as raised:
                            client.get("metadata/M015661")
                self.assertNotIsInstance(raised.exception, SourceMaintenanceError)
                self.assertFalse(raised.exception.retryable)
                self.assertEqual(opening.call_count, 1)
                sleeping.assert_not_called()
                self.assertIsNone(client.maintenance)
                self.assertFalse(client.cache)

    def test_valid_json_containing_maintenance_text_is_accepted_before_html_detection(self):
        value = {"StatusCode": 200, "Data": {"records": [], "announcement": MAINTENANCE_HTML.decode()}}
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", return_value=Response(json.dumps(value).encode())):
            with patch("housing_agent.sources._maintenance_notice", side_effect=AssertionError("must validate JSON first")):
                payload, record = client.get("resourceid", {"keyword": "maintenance"})
        self.assertEqual(payload, value)
        self.assertEqual(record["status"], "ok")
        self.assertIsNone(client.maintenance)

    def test_http_error_prefix_saved_with_size_limit_and_truncation_flag(self):
        sizes = []
        class BoundedBody(io.BytesIO):
            def read(self, size=-1):
                sizes.append(size)
                return super().read(size)
        body = MAINTENANCE_HTML + b" " * 50000
        error = HTTPError("https://tablebuilder.singstat.gov.sg/api/table/metadata/M015661",
                          502, "Bad Gateway", {"Content-Type": "text/html"}, BoundedBody(body))
        client = SingStatClient(self.root, retries=0)
        with patch("housing_agent.sources.urlopen", side_effect=error):
            with self.assertRaises(SourceMaintenanceError):
                client.get("metadata/M015661")
        self.assertEqual(sizes, [16 * 1024 + 1])
        attempt = client.records[0]["attempts"][0]
        saved = (self.root / attempt["error_body_prefix_file"]).read_bytes()
        self.assertEqual(saved, body[:16 * 1024])
        self.assertEqual(len(saved), 16 * 1024)
        self.assertTrue(attempt["error_body_prefix_truncated"])
        self.assertEqual(attempt["error_body_prefix_sha256"], hashlib.sha256(saved).hexdigest())

    def test_exception_retryable_contract_covers_timeout_schema_and_permanent_http(self):
        failures = [(TimeoutError("timed out"), True), (URLError("DNS failed"), True),
                    (self.error(b"not found", status=404), False)]
        for failure, retryable in failures:
            with self.subTest(failure=failure):
                client = SingStatClient(self.root, retries=0)
                with patch("housing_agent.sources.urlopen", side_effect=failure):
                    with self.assertRaises(SourceError) as raised:
                        client.get("metadata/M015661")
                self.assertEqual(raised.exception.retryable, retryable)
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", return_value=Response(b'{"StatusCode":200}')):
            with self.assertRaises(SourceError) as raised:
                client.get("metadata/M015661")
        self.assertFalse(raised.exception.retryable)

    def test_partial_http_success_is_rejected(self):
        item = Response((FIXTURES / "metadata_M015661.json").read_bytes())
        item.status = 206
        client = SingStatClient(self.root)
        with patch("housing_agent.sources.urlopen", return_value=item) as opening:
            with self.assertRaisesRegex(SourceError, "HTTP status: 206") as raised:
                client.get("metadata/M015661")
        self.assertFalse(raised.exception.retryable)
        self.assertEqual(opening.call_count, 1)
        self.assertFalse(client.cache)


if __name__ == "__main__":
    unittest.main()
