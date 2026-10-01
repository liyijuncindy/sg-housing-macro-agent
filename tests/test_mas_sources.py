"""Offline date-convention, closed-month and source-schema regression checks."""
from copy import deepcopy
import csv
import io
import unittest
from urllib.parse import parse_qs

from housing_agent.engine import evaluate_series
from housing_agent.mas_sources import MAS_URL, _daily_records, _form_payload, _monthly_observations, fetch_mas_series
from housing_agent.sources import SourceError


SPEC = {
    "table_id": "M700071", "row_id": "23", "expected_name": "Compounded Singapore Overnight Rate Average (SORA) - 3 Month",
    "expected_unit": "Per Cent Per Annum", "frequency": "M", "theme": "financing_cost",
    "definition": "Three-month compounded SORA at month-end.", "update_frequency": "Monthly",
    "change_kind": "basis_point", "mechanism": {
        "sales": "Rates may affect borrowing costs.", "rents": "The rental relationship may vary.",
        "lag": "Reset dates matter.", "limitations": "Not an individual mortgage offer.",
    },
}


def form(checkbox="ctl00$ContentPlaceHolder1$ColumnsCheckBoxList$16"):
    controls = []
    for name, values in {
        "StartYearDropDownList": ["2005", "2025", "2026"],
        "EndYearDropDownList": ["2005", "2025", "2026"],
        "StartMonthDropDownList": list(map(str, range(1, 13))),
        "EndMonthDropDownList": list(map(str, range(1, 13))),
    }.items():
        controls.append(f'<select name="ctl00$ContentPlaceHolder1${name}">' + "".join(f'<option value="{value}">{value}</option>' for value in values) + "</select>")
    return ("<html><form method='post' action='./DomesticInterestRates.aspx' id='form1'>"
            "<input type='hidden' name='__VIEWSTATE' value='public-viewstate'>"
            "<input type='hidden' name='__EVENTVALIDATION' value='public-validation'>"
            + "".join(controls)
            + f"<input type='checkbox' id='chosen-rate' name='{checkbox}'>"
            "<label for='chosen-rate'>3-month Compounded SORA</label>"
            "<input type='submit' name='ctl00$ContentPlaceHolder1$Button2' value='Download'>"
            "</form></html>").encode()


def csv_bytes(rows, header=None):
    text = io.StringIO(newline="")
    writer = csv.writer(text)
    writer.writerow(["MAS: Financial Database - Domestic Interest Rates"])
    writer.writerow(["Domestic Interest Rates (Daily)"])
    writer.writerow([])
    writer.writerow(header or ["SORA Value Date", "", "", "SORA Publication Date", "Compound SORA - 3 month"])
    writer.writerows(rows)
    writer.writerow([])
    writer.writerow(["Notes:"])
    writer.writerow(["The SORA Publication Date is the same date as the SORA Compounded Index Value Date."])
    return text.getvalue().encode()


ROWS = [
    ["2026", "Jul", "30", "31 Jul 2026", "1.1528"],
    ["", "", "31", "03 Aug 2026", "1.1354"],
    ["", "Aug", "28", "31 Aug 2026", "1.1805"],
    ["", "", "31", "01 Sep 2026", "1.1863"],
    ["", "Sep", "29", "30 Sep 2026", "1.2312"],
    ["", "", "30", "01 Oct 2026", "1.2336"],
]


class FakeClient:
    def __init__(self, body=None, form_body=None):
        self.body = body if body is not None else csv_bytes(ROWS)
        self.form_body = form_body if form_body is not None else form()
        self.calls = []
        self.saved_metadata = None

    def download(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return (self.body if kwargs.get("data") is not None else self.form_body), {
            "url": url, "raw_file": "raw/" + kwargs["name"] + kwargs["suffix"],
            "raw_sha256": "synthetic-hash", "retrieved_at": "2026-10-01T10:00:00+00:00",
        }

    def metadata(self, name, payload):
        self.saved_metadata = payload
        return {"raw_file": "raw/adapter.json", "raw_sha256": "synthetic-metadata-hash"}


class MASDateConventionTests(unittest.TestCase):
    def test_value_date_reproduces_month_end_while_publication_date_does_not(self):
        records = _daily_records(csv_bytes(ROWS))
        observations, omitted = _monthly_observations(records, "2026-09-30")
        by_period = {row["period"]: row for row in observations}
        self.assertEqual([row["value"] for row in observations], [1.1354, 1.1863, 1.2336])
        # Grouping by publication date would produce these different endpoints.
        wrong = {}
        for row in records:
            wrong[row["publication_date"].strftime("%Y-%m")] = row["value"]
        self.assertEqual(wrong["2026-07"], 1.1528)
        self.assertEqual(wrong["2026-08"], 1.1805)
        self.assertNotEqual(wrong["2026-07"], by_period["2026-07"]["value"])
        self.assertEqual(by_period["2026-07"]["sampling_date"], "2026-07-31")
        self.assertEqual(by_period["2026-07"]["source_publication_date"], "2026-08-03")
        self.assertEqual(by_period["2026-07"]["raw_sora_value_date"], ["", "", "31"])
        self.assertEqual(by_period["2026-07"]["raw_index"], 5)
        self.assertEqual(omitted, [])

    def test_missing_tail_month_is_omitted_instead_of_using_latest_available_day(self):
        observations, omitted = _monthly_observations(_daily_records(csv_bytes(ROWS[:-1])), "2026-09-30")
        self.assertEqual([row["period"] for row in observations], ["2026-07", "2026-08"])
        self.assertEqual(omitted[0]["period"], "2026-09")
        self.assertIn("closure", omitted[0]["reason"])

    def test_weekend_month_end_uses_last_business_day_without_bypassing_cutoff(self):
        records = _daily_records(csv_bytes([["2026", "May", "29", "01 Jun 2026", "1.0564"]]))
        observations, _ = _monthly_observations(records, "2026-05-31")
        self.assertEqual(observations[0]["period"], "2026-05")
        self.assertEqual(observations[0]["sampling_date"], "2026-05-29")
        self.assertNotIn("observation_date", observations[0])
        self.assertEqual(_monthly_observations(records, "2026-05-30")[0], [])

    def test_december_to_january_publication_closes_previous_calendar_year(self):
        records = _daily_records(csv_bytes([["2025", "Dec", "31", "02 Jan 2026", "1.1857"]]))
        observations, _ = _monthly_observations(records, "2025-12-31")
        self.assertEqual(observations[0]["period"], "2025-12")
        self.assertEqual(observations[0]["source_publication_date"], "2026-01-02")
        self.assertNotIn("published_at", observations[0])

    def test_null_month_end_is_not_replaced_by_an_earlier_finite_value(self):
        rows = deepcopy(ROWS[:2])
        rows[-1][-1] = "n.a."
        observations, _ = _monthly_observations(_daily_records(csv_bytes(rows)), "2026-07-31")
        self.assertIsNone(observations[0]["value"])
        self.assertEqual(observations[0]["raw_value"], "n.a.")

    def test_calendar_comparisons_remain_basis_points_after_adapter(self):
        result = fetch_mas_series(FakeClient(), SPEC, "2026-09-30")
        evaluation = evaluate_series(result, "2026-09-30")
        previous = next(c for c in evaluation["changes"] if c["comparison"] == "previous_period")
        self.assertEqual(previous["value"], 4.73)
        self.assertEqual(previous["unit"], "basis points")
        self.assertEqual(previous["evidence"][0]["source_publication_date"], "2026-10-01")


class MASFormatValidationTests(unittest.TestCase):
    def test_wrong_tenor_or_html_response_is_rejected(self):
        wrong = ["SORA Value Date", "", "", "SORA Publication Date", "Compound SORA - 1 month"]
        for body in (csv_bytes(ROWS, wrong), b"<html>Maintenance</html>"):
            with self.subTest(body=body[:80]), self.assertRaisesRegex(SourceError, "exact 3-month"):
                _daily_records(body)

    def test_bad_numeric_data_are_rejected_not_silently_dropped(self):
        for raw in ("NaN", "Infinity", "not a rate", "1,234.5"):
            rows = deepcopy(ROWS[:2])
            rows[-1][-1] = raw
            with self.subTest(raw=raw), self.assertRaises(SourceError):
                _daily_records(csv_bytes(rows))

    def test_duplicate_dates_or_impossible_date_order_are_rejected(self):
        duplicate_value = deepcopy(ROWS[:2])
        duplicate_value[-1][2] = "30"
        duplicate_publication = deepcopy(ROWS[:2])
        duplicate_publication[-1][3] = duplicate_publication[0][3]
        same_day_publication = [["2026", "Jul", "31", "31 Jul 2026", "1.1"]]
        for rows in (duplicate_value, duplicate_publication, same_day_publication):
            with self.subTest(rows=rows), self.assertRaises(SourceError):
                _daily_records(csv_bytes(rows))

    def test_missing_date_context_impossible_dates_and_truncated_rows_fail(self):
        for row in (["", "", "31", "01 Aug 2026", "1.1"],
                    ["2026", "Feb", "30", "01 Mar 2026", "1.1"],
                    ["2026", "Jul", "31", "bad-date", "1.1"],
                    ["2026", "Jul", "31", "03 Aug 2026"]):
            with self.subTest(row=row), self.assertRaises(SourceError):
                _daily_records(csv_bytes([row]))

    def test_date_context_rolls_forward_without_assuming_blank_is_missing(self):
        records = _daily_records(csv_bytes(ROWS))
        self.assertEqual(records[1]["value_date"].isoformat(), "2026-07-31")
        self.assertEqual(records[2]["value_date"].isoformat(), "2026-08-28")

    def test_official_multi_year_download_repeats_the_exact_header(self):
        header = ["SORA Value Date", "", "", "SORA Publication Date", "Compound SORA - 3 month"]
        rows = [["2025", "Dec", "31", "02 Jan 2026", "1.1857"], [], [], header,
                ["2026", "Jan", "02", "05 Jan 2026", "1.2"],
                ["", "", "30", "02 Feb 2026", "1.1502"]]
        records = _daily_records(csv_bytes(rows))
        observations, _ = _monthly_observations(records, "2026-01-31")
        self.assertEqual([row["period"] for row in observations], ["2025-12", "2026-01"])
        self.assertEqual(observations[-1]["value"], 1.1502)
        self.assertEqual(observations[-1]["raw_index"], 9)

    def test_new_header_resets_date_context_and_rejects_mixed_tenors(self):
        header = ["SORA Value Date", "", "", "SORA Publication Date", "Compound SORA - 3 month"]
        rows = [["2025", "Dec", "31", "02 Jan 2026", "1.1857"], header,
                ["", "", "02", "05 Jan 2026", "1.2"]]
        with self.assertRaisesRegex(SourceError, "Invalid MAS SORA value date"):
            _daily_records(csv_bytes(rows))
        rows[1] = [*header[:-1], "Compound SORA - 1 month"]
        rows[2] = ["2026", "Jan", "02", "05 Jan 2026", "1.2"]
        with self.assertRaises(SourceError):
            _daily_records(csv_bytes(rows))


class MASFetchTests(unittest.TestCase):
    def test_form_uses_observed_label_not_hardcoded_checkbox_position(self):
        client = FakeClient(form_body=form("ctl00$ContentPlaceHolder1$ColumnsCheckBoxList$99"))
        result = fetch_mas_series(client, SPEC, "2026-09-30")
        payload = parse_qs(client.calls[1][1]["data"].decode())
        self.assertEqual(payload["ctl00$ContentPlaceHolder1$ColumnsCheckBoxList$99"], ["on"])
        self.assertNotIn("ctl00$ContentPlaceHolder1$ColumnsCheckBoxList$16", payload)
        self.assertEqual(payload["ctl00$ContentPlaceHolder1$StartYearDropDownList"], ["2005"])
        self.assertEqual(payload["ctl00$ContentPlaceHolder1$EndMonthDropDownList"], ["9"])
        self.assertEqual(client.calls[1][1]["headers"]["Referer"], MAS_URL)
        self.assertEqual(result["id"], "M700071:23")
        self.assertEqual(result["provenance"]["raw_file"], "raw/mas_sora_daily.csv")
        self.assertIn("not the last publication-date", client.saved_metadata["transformation_note"])
        self.assertNotIn("published_at", result["observations"][-1])

    def test_incomplete_request_month_is_not_requested(self):
        payload, meta = _form_payload(form(), "2026-09-29")
        self.assertEqual(parse_qs(payload.decode())["ctl00$ContentPlaceHolder1$EndMonthDropDownList"], ["8"])
        self.assertEqual(meta["requested_end"], "2026-08")
        _, new_year = _form_payload(form(), "2026-01-01")
        self.assertEqual(new_year["requested_end"], "2025-12")

    def test_future_request_does_not_invent_a_form_year(self):
        _, meta = _form_payload(form(), "2030-12-31")
        self.assertEqual(meta["requested_end"], "2026-12")

    def test_missing_or_changed_form_controls_fail_before_post(self):
        bodies = [form().replace(b"public-viewstate", b""),
                  form().replace(b"3-month Compounded SORA", b"1-month Compounded SORA"),
                  form().replace(b"./DomesticInterestRates.aspx", b"https://untrusted.invalid/collect"),
                  b"<html>Maintenance</html>"]
        for body in bodies:
            client = FakeClient(form_body=body)
            with self.subTest(body=body[:60]), self.assertRaises(SourceError):
                fetch_mas_series(client, SPEC, "2026-09-30")
            self.assertEqual(len(client.calls), 1)

    def test_wrong_series_and_invalid_as_of_fail_before_network(self):
        for patch in ({"row_id": "22"}, {"frequency": "D"}, {"expected_unit": "Fraction"}, {"expected_name": "A renamed unrelated rate"}):
            client = FakeClient()
            with self.subTest(patch=patch), self.assertRaises(SourceError):
                fetch_mas_series(client, {**SPEC, **patch}, "2026-09-30")
            self.assertEqual(client.calls, [])
        for cutoff in ("20260930", "2026-02-30"):
            client = FakeClient()
            with self.subTest(cutoff=cutoff), self.assertRaises(SourceError):
                fetch_mas_series(client, SPEC, cutoff)
            self.assertEqual(client.calls, [])

    def test_no_closed_month_fails_instead_of_fabricating_month_end(self):
        client = FakeClient(body=csv_bytes(ROWS[:1]))
        with self.assertRaisesRegex(SourceError, "no verified complete"):
            fetch_mas_series(client, SPEC, "2026-09-30")
        self.assertIsNone(client.saved_metadata)


if __name__ == "__main__":
    unittest.main()
