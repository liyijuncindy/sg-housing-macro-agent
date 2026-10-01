"""Direct MOM CSV and XLSX adapters for two reviewed quarterly series.

The XLSX reader accepts the verified single-sheet MOM layout only; it does not
execute formulas or infer headers from arbitrary workbooks.
"""
from __future__ import annotations

import csv
import io
import math
import re
import zipfile
import xml.etree.ElementTree as ET

from .sources import SourceError

UNEMPLOYMENT_URL = "https://stats.mom.gov.sg/iMAS_Tables1/CSV/mrsd_11_Resident_unemployment_rate_n_number.csv"
INCOME_URL = "https://stats.mom.gov.sg/iMAS_Tables1/Time-Series-Table/mrsd_72_Mean_GMI_Emp_Res_Quarterly.xlsx"
UNEMPLOYMENT_PAGE = "https://stats.mom.gov.sg/Pages/Unemployment-Summary-Table.aspx"
INCOME_PAGE = "https://stats.mom.gov.sg/Pages/Income-Summary-Table.aspx"
INCOME_TITLE = "Mean Gross Monthly Income From Employment (Including Employer/Platform Operator CPF contributions and Excluding Bonus) of Employed Residents"
CSV_HEADERS = ("period", "quarter_annual", "residential_status", "seasonally_adjusted_unemployment_rate",
               "non-seasonally_adjusted_unemployment_rate", "seasonally_adjusted_unemployed_num",
               "non-seasonally_adjusted_unemployed_num", "annual_avg_unemployment_rate", "annual_avg_unemployed_num")
_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_REVIEWED_SPECS = {
    "M182342:2": {
        "expected_name": "Resident Unemployment Rate, (SA)", "expected_unit": "Per Cent",
        "frequency": "Q", "change_kind": "percentage_point", "seasonal_adjustment": "Seasonally Adjusted",
        "reference_month_day": None, "comparisons": None,
    },
    "M184101:1": {
        "expected_name": "Mean Gross Monthly Income From Employment (Including Employer CPF And Excluding Bonus) Of Employed Residents",
        "expected_unit": "Dollars", "frequency": "Q", "change_kind": "percent",
        "seasonal_adjustment": "Not labelled as seasonally adjusted", "reference_month_day": None,
        "comparisons": ["year_on_year"],
    },
}


def _clean(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def _number(raw: str, label: str, maximum: float | None = None) -> float | None:
    if raw.strip().lower() in {"", "na", "n.a."}:
        return None
    if not re.fullmatch(r"\d+(?:\.\d+)?", raw.strip()):
        raise SourceError(f"Unexpected MOM numeric value at {label}: {raw!r}")
    value = float(raw)
    if not math.isfinite(value) or value < 0 or maximum is not None and value > maximum:
        raise SourceError(f"MOM value outside the expected range at {label}")
    return value


def parse_unemployment_csv(body: bytes) -> list[dict]:
    """Select resident quarter-end SA rates, retaining MOM's published precision."""
    try:
        reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig"), newline=""), strict=True)
        if reader.fieldnames is None or len(reader.fieldnames) != len(CSV_HEADERS) or set(reader.fieldnames) != set(CSV_HEADERS):
            raise SourceError("MOM unemployment CSV columns changed; review the adapter")
        observations, seen = [], set()
        for index, row in enumerate(reader):
            if None in row or any(value is None for value in row.values()):
                raise SourceError("MOM unemployment CSV contains a malformed row")
            if row["quarter_annual"] != "quarter" or row["residential_status"] != "resident":
                continue
            raw_period = row["period"]
            match = re.fullmatch(r"(\d{4})-(03|06|09|12)", raw_period)
            if not match:
                raise SourceError(f"Unexpected MOM quarter-end period: {raw_period!r}")
            period = f"{match[1]}-Q{int(match[2]) // 3}"
            if period in seen:
                raise SourceError(f"Duplicate MOM unemployment period: {period}")
            seen.add(period)
            raw_value = row["seasonally_adjusted_unemployment_rate"]
            locator = f"CSV row {reader.line_num}, column seasonally_adjusted_unemployment_rate"
            observations.append({"period": period, "value": _number(raw_value, locator, 100),
                                 "raw_period": raw_period, "raw_value": raw_value,
                                 "raw_index": index, "raw_locator": locator})
    except (UnicodeDecodeError, csv.Error) as exc:
        raise SourceError("Cannot parse the official MOM unemployment CSV") from exc
    if not observations:
        raise SourceError("MOM CSV contains no quarterly resident unemployment rates")
    return observations


def _xlsx_cells(body: bytes) -> dict[str, str]:
    """Read shared/inline strings and scalar cells from verified Sheet1 only."""
    def xml(archive, name):
        info = archive.getinfo(name)
        if info.file_size > 2 * 1024 * 1024:
            raise SourceError("MOM XLSX XML member exceeds the size limit")
        raw = archive.read(name)
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise SourceError("MOM XLSX contains an unsupported XML declaration")
        return ET.fromstring(raw)

    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = archive.namelist()
            if len(names) > 200 or len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 10 * 1024 * 1024:
                raise SourceError("MOM workbook archive exceeds the verified format limits")
            book = xml(archive, "xl/workbook.xml")
            sheets = book.findall(f"{{{_MAIN}}}sheets/{{{_MAIN}}}sheet")
            if len(sheets) != 1 or sheets[0].get("name") != "Sheet1":
                raise SourceError("MOM income workbook must have the verified single Sheet1 layout")
            relation_id = sheets[0].get(f"{{{_REL}}}id")
            relationships = xml(archive, "xl/_rels/workbook.xml.rels")
            matching = [item for item in relationships if item.get("Id") == relation_id]
            if (len(matching) != 1 or matching[0].get("Target") != "worksheets/sheet1.xml"
                    or matching[0].get("TargetMode") == "External"):
                raise SourceError("MOM workbook worksheet relationship changed")
            shared = xml(archive, "xl/sharedStrings.xml")
            strings = ["".join(node.text or "" for node in item.iter(f"{{{_MAIN}}}t")) for item in shared]
            sheet = xml(archive, "xl/worksheets/sheet1.xml")
            cells = {}
            for cell in sheet.findall(f".//{{{_MAIN}}}sheetData/{{{_MAIN}}}row/{{{_MAIN}}}c"):
                address = cell.get("r", "")
                if not re.fullmatch(r"[A-Z]+[1-9]\d*", address) or address in cells:
                    raise SourceError("MOM workbook contains an invalid or duplicated cell address")
                if cell.find(f"{{{_MAIN}}}f") is not None:
                    raise SourceError("MOM income workbook contains formulas; cached values are not accepted")
                value = cell.find(f"{{{_MAIN}}}v")
                raw = value.text if value is not None and value.text is not None else ""
                kind = cell.get("t")
                if kind == "s":
                    if not raw.isdigit() or int(raw) >= len(strings):
                        raise SourceError("Invalid MOM XLSX shared-string reference")
                    raw = strings[int(raw)]
                elif kind == "inlineStr":
                    raw = "".join(node.text or "" for node in cell.iter(f"{{{_MAIN}}}t"))
                elif kind not in {None, "n"}:
                    raise SourceError("Unsupported MOM workbook cell type")
                cells[address] = raw
            return cells
    except SourceError:
        raise
    except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, OSError) as exc:
        raise SourceError("Cannot read the verified MOM income workbook structure") from exc


def parse_income_xlsx(body: bytes) -> tuple[list[dict], dict]:
    cells = _xlsx_cells(body)
    title = _clean(cells.get("A2", ""))
    if title.casefold() != INCOME_TITLE.casefold():
        raise SourceError("MOM income title or CPF/bonus definition changed; review the adapter")
    units = [value for address, value in cells.items() if re.fullmatch(r"[A-Z]+4", address) and value.strip()]
    if len(units) != 1 or units[0] != "Dollars":
        raise SourceError("MOM income workbook unit is not the verified Dollars")
    source_cells = [(address, value) for address, value in cells.items()
                    if re.fullmatch(r"[A-Z]+7", address) and value.strip()]
    if len(source_cells) != 1 or "Labour Force Survey, Manpower Research and Statistics Department, MOM" not in source_cells[0][1]:
        raise SourceError("MOM income workbook source attribution changed")
    notes = [(address, value) for address, value in cells.items()
             if re.fullmatch(r"A(?:[1-9]\d+)", address) and value.strip()]
    joined_notes = " ".join(value for _, value in notes)
    for required in ("Residents refer to Singapore Citizens and Permanent Residents", "income earned from employment",
                     "full-time National Servicemen", "same quarter of prior years", "platform workers", "p: preliminary"):
        if required.casefold() not in joined_notes.casefold():
            raise SourceError(f"MOM income workbook required definition or note changed: {required}")
    observations, seen, columns = [], set(), set()
    for address, raw_period in cells.items():
        match_address = re.fullmatch(r"([A-Z]+)5", address)
        if not match_address or not raw_period.strip():
            continue
        match = re.fullmatch(r"([1-4])Q\s+(\d{4})(p?)", _clean(raw_period), re.I)
        if not match:
            raise SourceError(f"Unexpected MOM income quarter label at {address}: {raw_period!r}")
        period = f"{match[2]}-Q{match[1]}"
        if period in seen:
            raise SourceError(f"Duplicate MOM income period: {period}")
        seen.add(period)
        column = match_address[1]
        columns.add(column)
        value_cell = column + "6"
        if value_cell not in cells:
            raise SourceError(f"MOM income value cell is missing: {value_cell}")
        raw_value = cells[value_cell]
        observations.append({"period": period, "value": _number(raw_value, value_cell),
                             "raw_period": raw_period, "raw_value": raw_value, "raw_index": len(observations),
                             "raw_locator": f"Sheet1!{value_cell} (period Sheet1!{address})",
                             "preliminary": bool(match[3])})
    if not observations:
        raise SourceError("MOM workbook contains no quarterly income observations")
    for address, value in cells.items():
        match = re.fullmatch(r"([A-Z]+)6", address)
        if match and value.strip() and match[1] not in columns:
            raise SourceError("MOM income value has no matching quarter header")
    return observations, {"official_title": title, "unit": "Dollars", "sheet": "Sheet1",
                          "source_attribution": source_cells[0][1], "notes": [value for _, value in notes],
                          "note_locators": [f"Sheet1!{address}" for address, _ in notes]}


def fetch_mom_series(client, spec: dict) -> dict:
    from .official_sources import build_series

    identifier = f"{spec['table_id']}:{spec['row_id']}"
    if identifier not in _REVIEWED_SPECS:
        raise SourceError(f"No reviewed MOM adapter for {identifier}")
    for field, expected in _REVIEWED_SPECS[identifier].items():
        if spec.get(field) != expected:
            raise SourceError(f"MOM reviewed mapping changed at {field} for {identifier}; review the adapter")
    if identifier == "M182342:2":
        body, raw = client.download(UNEMPLOYMENT_URL, name="mom_resident_unemployment", suffix=".csv")
        observations = parse_unemployment_csv(body)
        notes = ("Resident means Singapore citizens and permanent residents. This adapter selects quarter rows and the "
                 "seasonally_adjusted_unemployment_rate column, preserving the published CSV precision. It excludes annual averages "
                 "and unadjusted rates. Seasonal adjustment can be revised. The CSV does not provide observation publication dates "
                 "or preliminary flags; none are inferred. Definitions and current release notes: " + UNEMPLOYMENT_PAGE)
        metadata = client.metadata("mom_resident_unemployment", {"metadata_origin": "Adapter-generated description of an official MOM CSV, not official API metadata",
                    "source_url": UNEMPLOYMENT_PAGE, "download_url": UNEMPLOYMENT_URL, "columns": list(CSV_HEADERS),
                    "selected_filters": {"quarter_annual": "quarter", "residential_status": "resident"},
                    "value_column": "seasonally_adjusted_unemployment_rate", "notes": notes})
        return build_series(spec, raw, metadata, observations, source_url=UNEMPLOYMENT_PAGE,
                            source_agency="MINISTRY OF MANPOWER", source_provider="MOM official CSV",
                            source_footnote=notes, row_footnote=notes,
                            source_updated_at="Not supplied in the CSV", seasonal_adjustment="Seasonally Adjusted",
                            table_title="Resident unemployment rate and number, official MOM CSV")
    if identifier == "M184101:1":
        body, raw = client.download(INCOME_URL, name="mom_mean_employment_income", suffix=".xlsx")
        observations, details = parse_income_xlsx(body)
        notes = " ".join(details["notes"])
        metadata = client.metadata("mom_mean_employment_income", {"metadata_origin": "Adapter-generated description extracted from an official MOM workbook, not official API metadata",
                    "source_url": INCOME_PAGE, "download_url": INCOME_URL, **details,
                    "layout": "Sheet1: title A2, unit row 4, quarter labels row 5, dollar levels row 6, source row 7, notes column A",
                    "preliminary_marker": "p in the quarter label; retained in raw_period and preliminary",
                    "mapping_note": "Mapped to the reviewed SingStat series ID; publisher title explicitly includes platform operator CPF contributions."})
        return build_series(spec, raw, metadata, observations, name=details["official_title"], source_url=INCOME_PAGE,
                            source_agency="MINISTRY OF MANPOWER", source_provider="MOM official XLSX",
                            table_title=details["official_title"],
                            definition="Mean gross monthly employment income of employed residents, including employer/platform operator CPF contributions and excluding bonus; before employee CPF and personal income tax deductions.",
                            source_footnote=notes, row_footnote=notes, source_updated_at="Not supplied as a release timestamp in the workbook",
                            seasonal_adjustment="Not labelled as seasonally adjusted", comparisons=["year_on_year"])
    raise SourceError(f"No reviewed MOM adapter for {identifier}")
