"""Public MAS download adapter for the reviewed month-end compounded SORA row.

The daily CSV has two different date conventions. Its SORA Value Date, not its
SORA Publication Date, reproduces SingStat M700071:23 month-end observations.
No monthly averages or unfinished-month observations are substituted.
"""
from __future__ import annotations

import calendar
import csv
from datetime import date
from html.parser import HTMLParser
import io
import math
import re
from urllib.parse import urlencode, urljoin

from .official_sources import build_series
from .sources import SourceError


MAS_URL = "https://eservices.mas.gov.sg/statistics/dir/DomesticInterestRates.aspx"
_PREFIX = "ctl00$ContentPlaceHolder1$"
_MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_abbr) if name}
_CSV_HEADER = ["SORA Value Date", "", "", "SORA Publication Date", "Compound SORA - 3 month"]
_EXPECTED_NAME = "Compounded Singapore Overnight Rate Average (SORA) - 3 Month"
_TRANSFORMATION = (
    "Group daily records by the calendar month of SORA Value Date and select the "
    "last value-date record, not the last publication-date record and not an average. "
    "The month must end on or before as_of. Its last record's SORA Publication Date "
    "must cross that month-end, providing conservative evidence that the last "
    "business-day record was received. Otherwise omit the month instead of "
    "substituting an earlier value. This can temporarily omit the newest month. "
    "A null final value remains null. The original daily CSV dates and row position "
    "are retained. Source publication dates are CSV labels, also described by MAS "
    "as compounded-index value dates; they do not prove when the historical "
    "three-month series was first available. No observation published_at is invented."
)


def _cutoff(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise SourceError("MAS as_of must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SourceError("MAS as_of is not a valid date") from exc


class _DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_form = False
        self.found_form = False
        self.action = None
        self.method = None
        self.hidden = {}
        self.inputs = {}
        self.selects = {}
        self.labels = {}
        self.download_name = None
        self._select = None
        self._label = None
        self._label_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and attrs.get("id") == "form1":
            if self.found_form:
                raise SourceError("MAS page contains duplicate download forms")
            self.in_form = self.found_form = True
            self.action = attrs.get("action", "")
            self.method = attrs.get("method", "").lower()
        if not self.in_form:
            return
        if tag == "input":
            if attrs.get("id"):
                self.inputs[attrs["id"]] = attrs
            if attrs.get("type", "").lower() == "hidden" and attrs.get("name"):
                self.hidden[attrs["name"]] = attrs.get("value", "")
            if attrs.get("type", "").lower() == "submit" and attrs.get("value", "").strip() == "Download":
                self.download_name = attrs.get("name")
        elif tag == "select":
            self._select = attrs.get("name")
            if self._select:
                self.selects[self._select] = set()
        elif tag == "option" and self._select:
            self.selects[self._select].add(attrs.get("value", ""))
        elif tag == "label":
            self._label = attrs.get("for")
            self._label_text = []

    def handle_data(self, value):
        if self.in_form and self._label:
            self._label_text.append(value)

    def handle_endtag(self, tag):
        if tag == "label" and self._label:
            self.labels[self._label] = " ".join("".join(self._label_text).split())
            self._label = None
        elif tag == "select":
            self._select = None
        elif tag == "form":
            self.in_form = False


def _form_payload(body: bytes, as_of: str) -> tuple[bytes, dict]:
    cutoff = _cutoff(as_of)
    # Ask only for complete calendar months. A boundary day's CSV publication
    # can be in the next month, which is required by the closure check below.
    end_year, end_month = cutoff.year, cutoff.month
    if cutoff.day != calendar.monthrange(cutoff.year, cutoff.month)[1]:
        end_month -= 1
        if end_month == 0:
            end_year, end_month = end_year - 1, 12
    if end_year < 2005:
        raise SourceError("The MAS SORA adapter starts in 2005; no complete requested month is available")
    form = _DownloadForm()
    try:
        form.feed(body.decode("utf-8-sig"))
    except UnicodeError as exc:
        raise SourceError("MAS download form is not valid UTF-8") from exc
    if not form.found_form or form.method != "post" or urljoin(MAS_URL, form.action or "") != MAS_URL:
        raise SourceError("MAS public download form is missing or its action changed")
    if not all(form.hidden.get(key) for key in ("__VIEWSTATE", "__EVENTVALIDATION")):
        raise SourceError("MAS download form is missing required public form state")
    matching = [form.inputs.get(key) for key, text in form.labels.items() if text == "3-month Compounded SORA"]
    if len(matching) != 1 or not matching[0] or matching[0].get("type", "").lower() != "checkbox" or not matching[0].get("name"):
        raise SourceError("MAS form does not identify exactly one 3-month Compounded SORA checkbox")
    if not form.download_name:
        raise SourceError("MAS form has no Download submit control")
    start_years = form.selects.get(_PREFIX + "StartYearDropDownList", set())
    end_years = form.selects.get(_PREFIX + "EndYearDropDownList", set())
    if "2005" not in start_years or not end_years or any(not value.isdigit() for value in end_years):
        raise SourceError("MAS year controls changed or cannot supply the requested history")
    latest_form_year = max(map(int, end_years))
    if end_year > latest_form_year:
        end_year, end_month = latest_form_year, 12
    choices = {
        "StartYearDropDownList": "2005", "EndYearDropDownList": str(end_year),
        "StartMonthDropDownList": "1", "EndMonthDropDownList": str(end_month),
    }
    for control, value in choices.items():
        if value not in form.selects.get(_PREFIX + control, set()):
            raise SourceError(f"MAS date control cannot represent the requested {control}")
    values = {**form.hidden, **{_PREFIX + key: value for key, value in choices.items()},
              matching[0]["name"]: matching[0].get("value", "on"), form.download_name: "Download"}
    return urlencode(values).encode("utf-8"), {
        "requested_start": "2005-01", "requested_end": f"{end_year:04d}-{end_month:02d}",
        "selected_label": "3-month Compounded SORA", "selected_control": matching[0]["name"],
    }


def _publication_date(raw: str) -> date:
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", raw.strip())
    if match is None or match[2].lower() not in _MONTHS:
        raise SourceError("MAS CSV contains an invalid SORA publication date")
    try:
        return date(int(match[3]), _MONTHS[match[2].lower()], int(match[1]))
    except ValueError as exc:
        raise SourceError("MAS CSV contains an impossible SORA publication date") from exc


def _daily_records(body: bytes) -> list[dict]:
    try:
        rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig")), strict=True))
    except (UnicodeError, csv.Error) as exc:
        raise SourceError("MAS download is not a valid UTF-8 CSV") from exc
    headers = [index for index, row in enumerate(rows) if [field.strip() for field in row] == _CSV_HEADER]
    if not headers:
        raise SourceError("MAS CSV must contain the exact 3-month compounded SORA date/value columns")
    records, value_dates, publication_dates = [], set(), set()
    year = month = None
    for index in range(headers[0] + 1, len(rows)):
        raw = rows[index]
        if not raw or not any(field.strip() for field in raw):
            continue
        # The official multi-year download repeats its header at each year.
        # Only an identical header opens a new block, and its first date must
        # supply fresh year/month context rather than inheriting the prior year.
        if [field.strip() for field in raw] == _CSV_HEADER:
            year = month = None
            continue
        # Only known explanatory footers end the data region; a truncated or
        # otherwise malformed date row must fail rather than disappear.
        first = raw[0].strip()
        if first.lower().startswith(("notes", "note:", "after a review of the market", "the singapore overnight", "the sora publication", "for the singapore interbank")):
            break
        if len(raw) != 5:
            raise SourceError(f"Unexpected MAS CSV record width at row {index + 1}")
        fields = [field.strip() for field in raw]
        try:
            if fields[0]:
                if not re.fullmatch(r"\d{4}", fields[0]):
                    raise ValueError("year")
                year = int(fields[0])
            if fields[1]:
                month = _MONTHS[fields[1].lower()]
            if year is None or month is None or not re.fullmatch(r"\d{1,2}", fields[2]):
                raise ValueError("missing date context")
            value_date = date(year, month, int(fields[2]))
        except (ValueError, KeyError) as exc:
            raise SourceError(f"Invalid MAS SORA value date at CSV row {index + 1}") from exc
        publication_date = _publication_date(fields[3])
        if publication_date <= value_date:
            raise SourceError("MAS SORA publication date must follow its value date")
        if value_date in value_dates or publication_date in publication_dates:
            raise SourceError("Duplicate MAS SORA value/publication date")
        value_dates.add(value_date)
        publication_dates.add(publication_date)
        if fields[4].lower() in {"", "na", "n.a", "n.a.", "-"}:
            value = None
        else:
            try:
                value = float(fields[4])
            except ValueError as exc:
                raise SourceError(f"Nonnumeric compounded SORA at CSV row {index + 1}") from exc
            if not math.isfinite(value):
                raise SourceError(f"Non-finite compounded SORA at CSV row {index + 1}")
        records.append({"value_date": value_date, "publication_date": publication_date,
                        "value": value, "raw_value": raw[4], "raw_index": index,
                        "raw_sora_value_date": raw[:3], "raw_sora_publication_date": raw[3]})
    if not records:
        raise SourceError("MAS CSV contains no daily observations")
    records.sort(key=lambda record: record["value_date"])
    if any(right["publication_date"] <= left["publication_date"] for left, right in zip(records, records[1:])):
        raise SourceError("MAS value and publication dates are not monotonically aligned")
    return records


def _monthly_observations(records: list[dict], as_of: str) -> tuple[list[dict], list[dict]]:
    cutoff = _cutoff(as_of)
    final_records = {}
    for record in records:
        key = record["value_date"].strftime("%Y-%m")
        if key not in final_records or record["value_date"] > final_records[key]["value_date"]:
            final_records[key] = record
    observations, omitted = [], []
    for period, record in sorted(final_records.items()):
        value_date = record["value_date"]
        period_end = date(value_date.year, value_date.month, calendar.monthrange(value_date.year, value_date.month)[1])
        if period_end > cutoff:
            omitted.append({"period": period, "reason": "calendar month has not ended by as_of"})
            continue
        if record["publication_date"] <= period_end:
            omitted.append({"period": period, "reason": "no month-end closure evidence; final daily record publishes within the same month"})
            continue
        observations.append({
            "period": period, "value": record["value"],
            "raw_period": " ".join(record["raw_sora_value_date"]),
            "raw_value": record["raw_value"], "raw_index": record["raw_index"],
            "sampling_date": value_date.isoformat(), "source_value_date": value_date.isoformat(),
            "source_publication_date": record["publication_date"].isoformat(),
            "raw_sora_value_date": record["raw_sora_value_date"],
            "raw_sora_publication_date": record["raw_sora_publication_date"],
            "raw_locator": f"CSV record {record['raw_index'] + 1}, column 5 (Compound SORA - 3 month)",
            "sampling_rule": "last SORA Value Date in a verified closed calendar month",
        })
    return observations, omitted


def fetch_mas_series(client, spec: dict, as_of: str) -> dict:
    """Fetch audited MAS daily data and reproduce the reviewed month-end series."""
    if (spec.get("table_id"), str(spec.get("row_id")), spec.get("frequency"), spec.get("expected_unit")) != (
        "M700071", "23", "M", "Per Cent Per Annum"
    ) or spec.get("change_kind") != "basis_point" or spec.get("expected_name") != _EXPECTED_NAME:
        raise SourceError("The MAS adapter supports only reviewed M700071:23 monthly 3-month compounded SORA")
    _cutoff(as_of)
    form_body, form_record = client.download(MAS_URL, name="mas_sora_form", suffix=".html")
    payload, request_metadata = _form_payload(form_body, as_of)
    csv_body, raw_record = client.download(
        MAS_URL, name="mas_sora_daily", suffix=".csv", data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": MAS_URL},
    )
    records = _daily_records(csv_body)
    observations, omitted = _monthly_observations(records, as_of)
    if not observations:
        raise SourceError("MAS returned no verified complete month-end SORA observations for this cutoff")
    metadata = {
        "adapter": "mas_compounded_sora_3m_month_end", "as_of": as_of,
        "source_page": MAS_URL, "reviewed_equivalent_series": "M700071:23",
        "source_columns": _CSV_HEADER, "source_frequency": "Daily business-day observations",
        "output_frequency": "M", "unit": "Per Cent Per Annum",
        "transformation_note": _TRANSFORMATION, "request": request_metadata,
        "source_form": form_record, "source_csv": raw_record,
        "daily_record_count": len(records), "monthly_record_count": len(observations),
        "first_source_value_date": records[0]["value_date"].isoformat(),
        "last_source_value_date": records[-1]["value_date"].isoformat(),
        "last_source_publication_date": records[-1]["publication_date"].isoformat(),
        "omitted_months": omitted,
        "validation_basis": "Date convention was checked against the saved official M700071:23 series over all overlapping non-null observations; this adapter never obtains values from that snapshot.",
    }
    metadata_record = client.metadata("mas_sora_3m", metadata)
    return build_series(
        spec, raw_record, metadata_record, observations,
        source_agency="MONETARY AUTHORITY OF SINGAPORE",
        source_provider="MAS direct public daily CSV; verified month-end sampling",
        table_title="Domestic Interest Rates (Daily): Compound SORA - 3 month",
        source_frequency="Daily business-day observations", transformation_note=_TRANSFORMATION,
        update_frequency="MAS publishes daily business-day observations; this adapter derives verified completed calendar-month endpoints. Source publication/index dates are retained separately.",
        availability_note="Latest captured vintage. SORA publication/index-value dates in the daily CSV do not establish first publication of the historical compounded series; months without closure evidence are omitted.",
        row_footnote="Monthly sampling uses the last SORA Value Date, not the SORA Publication Date. Both dates are preserved in observations. " + _TRANSFORMATION,
    )
