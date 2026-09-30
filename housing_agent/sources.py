"""Bounded, recorded access to SingStat's public table and discovery APIs."""
from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .storage import sha256_bytes, utc_now, write_json

BASE = "https://tablebuilder.singstat.gov.sg/api/table/"
FREQUENCIES = {"Annual": "A", "Quarterly": "Q", "Monthly": "M"}
MISSING = {"", "na", "n.a.", "n.a", "-", "..", "...", "null", "none", "not available"}
MONTHS = {name.lower(): i for i, name in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


class SourceError(RuntimeError):
    pass


class SingStatClient:
    def __init__(self, run_dir: Path, timeout: float = 20, retries: int = 2):
        self.run_dir = run_dir
        self.timeout = timeout
        self.retries = retries
        self.records: list[dict] = []
        self.cache: dict[str, tuple[dict, dict]] = {}

    def get(self, endpoint: str, params: dict | None = None) -> tuple[dict, dict]:
        if not re.fullmatch(r"(?:resourceid|(?:tabledata|metadata)/[A-Za-z0-9]+)", endpoint):
            raise SourceError("Unsupported source endpoint")
        url = BASE + endpoint + ("?" + urlencode(params) if params else "")
        if url in self.cache:
            return self.cache[url]
        record = {"url": url, "retrieved_at": utc_now(), "attempts": [], "status": "pending"}
        self.records.append(record)
        token = sha256_bytes(url.encode())[:16]
        raw_path = self.run_dir / "raw" / (endpoint.replace("/", "_") + "_" + token + ".json")
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                req = Request(url, headers={"User-Agent": "HousingResearchAgent/0.1 (public statistical research)", "Accept": "application/json"})
                with urlopen(req, timeout=self.timeout) as response:
                    body = response.read(20 * 1024 * 1024 + 1)
                    if len(body) > 20 * 1024 * 1024:
                        raise SourceError("Response exceeds the download size limit")
                    payload = json.loads(body)
                    if not isinstance(payload, dict) or not isinstance(payload.get("Data"), dict):
                        raise SourceError("Unexpected SingStat response schema: missing Data object")
                    if payload.get("StatusCode") not in (200, "200"):
                        raise SourceError(f"SingStat API returned failure status: {payload.get('StatusCode')}")
                    record["content_type"] = response.headers.get("Content-Type", "unknown")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(body)
                record.update(status="ok", completed_at=utc_now(), raw_file=str(raw_path.relative_to(self.run_dir)), raw_sha256=sha256_bytes(body))
                record["attempts"].append({"attempt": attempt + 1, "status": "ok"})
                self.cache[url] = (payload, record)
                return payload, record
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, SourceError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                record["attempts"].append({"attempt": attempt + 1, "status": "failed", "error": last_error})
                # A schema error or a permanent HTTP error cannot be fixed by blind retries.
                if isinstance(exc, (ValueError, SourceError)) or isinstance(exc, HTTPError) and exc.code not in {408, 429, 500, 502, 503, 504}:
                    break
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 4))
        record.update(status="failed", error=last_error)
        raise SourceError(f"Failed to retrieve {url}: {last_error}")

    def discover(self, query: str) -> list[dict]:
        payload, _ = self.get("resourceid", {"keyword": query, "searchOption": "all"})
        records = payload["Data"].get("records")
        if not isinstance(records, list):
            raise SourceError("Discovery records must be a list")
        return records

    def save_records(self):
        write_json(self.run_dir / "retrievals.json", self.records)


def canonical_period(raw: str, frequency: str) -> str:
    raw = str(raw).strip()
    if frequency == "A" and re.fullmatch(r"\d{4}", raw):
        return raw
    if frequency == "Q":
        match = re.fullmatch(r"(\d{4})\s*([1-4])Q", raw, re.I)
        if match:
            return f"{match[1]}-Q{match[2]}"
        match = re.fullmatch(r"(\d{4})\s*[- ]?\s*(?:Q|Qtr|Quarter)\s*([1-4])", raw, re.I)
        if match:
            return f"{match[1]}-Q{match[2]}"
        match = re.fullmatch(r"([1-4])Q\s*(\d{4})", raw, re.I)
        if match:
            return f"{match[2]}-Q{match[1]}"
    if frequency == "M":
        match = re.fullmatch(r"(\d{4})[- ](\d{1,2})", raw)
        if match and 1 <= int(match[2]) <= 12:
            return f"{match[1]}-{int(match[2]):02d}"
        match = re.fullmatch(r"(\d{4})\s+([A-Za-z]+)", raw)
        if match and match[2][:3].lower() in MONTHS:
            return f"{match[1]}-{MONTHS[match[2][:3].lower()]:02d}"
    raise SourceError(f"Unsupported {frequency} observation period: {raw!r}")


def parse_value(raw: object) -> float | None:
    if raw is None or str(raw).strip().lower() in MISSING:
        return None
    try:
        value = float(str(raw).replace(",", "").strip())
    except ValueError as exc:
        raise SourceError(f"Unexpected nonnumeric observation: {raw!r}") from exc
    if not math.isfinite(value):
        raise SourceError("Non-finite numeric observation")
    return value


def fetch_series(client: SingStatClient, spec: dict) -> dict:
    table = spec["table_id"]
    row_id = str(spec["row_id"])
    metadata, meta_record = client.get(f"metadata/{table}")
    meta = metadata["Data"].get("records", metadata["Data"])
    if not isinstance(meta, dict):
        raise SourceError("Unexpected metadata record structure")
    # Filter on the server. Unfiltered tables silently truncate at 5,000 cells.
    payload, raw_record = client.get(f"tabledata/{table}", {"seriesNoORrowNo": row_id, "limit": 5000})
    data = payload["Data"]
    if meta.get("id") != table or data.get("id") != table:
        raise SourceError("Metadata or data table identity does not match the requested table")
    if meta.get("frequency") != data.get("frequency"):
        raise SourceError("Metadata and data frequency disagree")
    if meta.get("dataLastUpdated") != data.get("dataLastUpdated"):
        raise SourceError("Metadata and observations belong to different table updates; retry in a new run")
    meta_rows = [r for r in meta.get("row", []) if str(r.get("seriesNo", r.get("rowNo"))) == row_id]
    if len(meta_rows) != 1:
        raise SourceError("Metadata must contain exactly one matching source row")
    rows = [r for r in data.get("row", []) if str(r.get("seriesNo", r.get("rowNo"))) == row_id]
    if len(rows) != 1:
        raise SourceError(f"Expected one exact row {row_id} in {table}, got {len(rows)}")
    row = rows[0]
    if any(meta_rows[0].get(key) != row.get(key) for key in ("rowText", "uoM")):
        raise SourceError("Metadata and observation row name or unit disagree")
    if row.get("rowText") != spec["expected_name"] or row.get("uoM") != spec["expected_unit"]:
        raise SourceError(f"Series definition or unit changed for {table}:{row_id}; review catalogue before using")
    frequency = FREQUENCIES.get(data.get("frequency"))
    if frequency != spec["frequency"]:
        raise SourceError(f"Frequency changed or unsupported for {table}:{row_id}")
    columns = row.get("columns")
    if not isinstance(columns, list) or not columns:
        raise SourceError("Series contains no observations")
    if len(columns) >= 5000:
        raise SourceError("Series may be truncated; pagination is required")
    observations = []
    for index, col in enumerate(columns):
        period = canonical_period(col["key"], frequency)
        obs = {"period": period, "value": parse_value(col.get("value")), "raw_period": col["key"], "raw_value": col.get("value"), "raw_index": index}
        if spec.get("reference_month_day") and frequency == "A":
            obs["observation_date"] = f"{period}-{spec['reference_month_day']}"
        observations.append(obs)
    return {
        "id": f"{table}:{row_id}", "name": row["rowText"], "theme": spec["theme"],
        "selection_family": spec.get("selection_family", spec["theme"]),
        "definition": spec["definition"], "unit": row["uoM"], "frequency": frequency,
        "update_frequency": spec["update_frequency"], "source_url": f"https://tablebuilder.singstat.gov.sg/table/TS/{table}",
        "api_url": raw_record["url"], "table_id": table, "row_id": row_id,
        "table_title": data.get("title", meta.get("title", "Unknown")),
        "source_agency": data.get("datasource", "Unknown"), "retrieved_at": raw_record["retrieved_at"],
        "source_updated_at": data.get("dataLastUpdated"), "source_footnote": data.get("footnote", ""),
        "row_footnote": row.get("footnote", ""), "change_kind": spec["change_kind"],
        "scope": spec.get("scope", "See source definition"), "seasonal_adjustment": spec.get("seasonal_adjustment", "Not established"),
        "reference_month_day": spec.get("reference_month_day"),
        **({"comparisons": spec["comparisons"]} if "comparisons" in spec else {}),
        "provenance": {"raw_file": raw_record["raw_file"], "raw_sha256": raw_record["raw_sha256"], "metadata_file": meta_record["raw_file"], "metadata_sha256": meta_record["raw_sha256"]},
        "mechanism": spec["mechanism"], "observations": observations,
        "availability_note": "Latest downloaded vintage. Table update date is not an observation release date; historical information availability is not reconstructed.",
    }
