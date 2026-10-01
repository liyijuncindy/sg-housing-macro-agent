"""Bounded, recorded access to SingStat's public table and discovery APIs."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from http.client import HTTPException
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
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
ERROR_PREFIX_BYTES = 16 * 1024
TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


class SourceError(RuntimeError):
    retryable = False


class SourceUnavailableError(SourceError):
    """This request exhausted bounded retries for a temporary transport failure."""

    retryable = True


class SourceMaintenanceError(SourceError):
    """This request still returned a standalone current-maintenance notice."""

    retryable = True


def _response_details(status, headers) -> dict:
    allowed = {}
    for name in ("Date", "Server", "Content-Type", "Cache-Control", "Cache-Status", "X-Cache", "Age", "Retry-After"):
        value = headers.get(name) if headers is not None else None
        if value is not None:
            allowed[name.lower()] = str(value)[:1024]
    return {"http_status": status, "response_headers": allowed,
            "content_type": allowed.get("content-type", "unknown")}


class _VisibleHTML(HTMLParser):
    """Extract notice text without treating scripts, metadata or comments as prose."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        if tag in {"head", "script", "style", "template"}:
            self.ignored.append(tag)

    def handle_endtag(self, tag):
        if tag in self.ignored:
            self.ignored = self.ignored[:self.ignored.index(tag)]

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def _maintenance_notice(body: bytes) -> str | None:
    # Deliberately narrow: the whole visible page must be the observed current
    # notice. A normal page quoting an old/future notice is not source status.
    text = body[:ERROR_PREFIX_BYTES].decode("utf-8", errors="replace")
    if not re.match(r"\s*(?:<!doctype\s+html\b|<html\b|<body\b)", text, re.I):
        return None
    parser = _VisibleHTML()
    parser.feed(text)
    visible = " ".join(" ".join(parser.parts).split())
    pattern = (r"(?:The )?SingStat Table Builder(?: and SANDRA(?:\s*\([^)]{0,140}\))?)? "
               r"(?:is|are) currently undergoing maintenance\.?"
               r"(?: We will work to complete the maintenance work ASAP\.)?"
               r"(?: Thank you for your patience\.)?")
    return visible[:600] if re.fullmatch(pattern, visible, re.I) else None


class SingStatClient:
    def __init__(self, run_dir: Path, timeout: float = 20, retries: int = 2):
        if not isinstance(retries, int) or isinstance(retries, bool) or not 0 <= retries <= 10:
            raise ValueError("retries must be an integer between 0 and 10")
        self.run_dir = run_dir
        self.timeout = timeout
        self.retries = retries
        self.records: list[dict] = []
        self.cache: dict[str, tuple[dict, dict]] = {}
        self.maintenance: dict | None = None

    def get(self, endpoint: str, params: dict | None = None) -> tuple[dict, dict]:
        if not re.fullmatch(r"(?:resourceid|(?:tabledata|metadata)/[A-Za-z0-9]+)", endpoint):
            raise SourceError("Unsupported source endpoint")
        url = BASE + endpoint + ("?" + urlencode(params) if params else "")
        # This attribute is last-request evidence, never a global circuit breaker.
        self.maintenance = None
        if url in self.cache:
            return self.cache[url]
        record = {"url": url, "retrieved_at": utc_now(), "attempts": [], "status": "pending"}
        self.records.append(record)
        token = sha256_bytes(url.encode())[:16]
        raw_path = self.run_dir / "raw" / (endpoint.replace("/", "_") + "_" + token + ".json")
        last_error = None
        last_exception = None
        for attempt in range(self.retries + 1):
            details = {}
            attempt_record = {"attempt": attempt + 1, "retrieved_at": utc_now()}
            body = b""
            prefix_truncated = False
            notice = None
            try:
                req = Request(url, headers={"User-Agent": "HousingResearchAgent/0.1 (public statistical research)", "Accept": "application/json"})
                with urlopen(req, timeout=self.timeout) as response:
                    details = _response_details(getattr(response, "status", 200), response.headers)
                    body = response.read(MAX_RESPONSE_BYTES + 1)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise SourceError("Response exceeds the download size limit")
                    if details["http_status"] != 200:
                        raise SourceError(f"Unexpected successful HTTP status: {details['http_status']}")
                    try:
                        payload = json.loads(body)
                    except (ValueError, UnicodeDecodeError):
                        notice = _maintenance_notice(body)
                        if notice is not None:
                            raise SourceMaintenanceError("This request returned a current maintenance notice: " + notice) from None
                        raise SourceError("Expected a SingStat JSON response; unrecognised non-JSON content") from None
                    if not isinstance(payload, dict) or not isinstance(payload.get("Data"), dict):
                        raise SourceError("Unexpected SingStat response schema: missing Data object")
                    if payload.get("StatusCode") not in (200, "200"):
                        raise SourceError(f"SingStat API returned failure status: {payload.get('StatusCode')}")
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(body)
                record.update(status="ok", completed_at=utc_now(), raw_file=str(raw_path.relative_to(self.run_dir)), raw_sha256=sha256_bytes(body), **details)
                record["attempts"].append({**attempt_record, "completed_at": utc_now(), "status": "ok", **details})
                self.maintenance = None
                self.cache[url] = (payload, record)
                return payload, record
            except (HTTPError, URLError, HTTPException, TimeoutError, OSError, ValueError, SourceError) as exc:
                if isinstance(exc, HTTPException):
                    partial = getattr(exc, "partial", None)
                    if isinstance(partial, bytes):
                        body = partial
                    attempt_record["error_body_incomplete"] = True
                if isinstance(exc, HTTPError):
                    details = _response_details(exc.code, exc.headers)
                    if exc.fp is not None:
                        try:
                            body = exc.read(ERROR_PREFIX_BYTES + 1)
                            prefix_truncated = len(body) > ERROR_PREFIX_BYTES
                        except (HTTPException, OSError, ValueError, AttributeError) as read_error:
                            partial = getattr(read_error, "partial", None)
                            if isinstance(partial, bytes):
                                body = partial
                            attempt_record.update(error_body_incomplete=True,
                                                  error_body_read_error=f"{type(read_error).__name__}: {read_error}")
                        finally:
                            exc.close()
                    notice = _maintenance_notice(body) if exc.code in TRANSIENT_HTTP else None
                    if notice is not None:
                        exc = SourceMaintenanceError("This request returned a current maintenance notice: " + notice)
                last_error = f"{type(exc).__name__}: {exc}"
                last_exception = exc
                attempt_record.update(status="failed", error=last_error, completed_at=utc_now(), **details)
                if body:
                    prefix = body[:ERROR_PREFIX_BYTES]
                    suffix = ".html" if prefix.lstrip().startswith(b"<") else ".bin"
                    failure_path = self.run_dir / "raw" / f"failed_{endpoint.replace('/', '_')}_{token}_{len(self.records):03d}_{attempt + 1}{suffix}"
                    failure_path.parent.mkdir(parents=True, exist_ok=True)
                    failure_path.write_bytes(prefix)
                    attempt_record.update(error_body_prefix_file=str(failure_path.relative_to(self.run_dir)),
                                          error_body_prefix_sha256=sha256_bytes(prefix), error_body_prefix_bytes=len(prefix),
                                          error_body_prefix_truncated=prefix_truncated or len(body) > ERROR_PREFIX_BYTES)
                if notice is not None:
                    attempt_record.update(maintenance_notice=notice, maintenance_source_url=url,
                                          maintenance_body_prefix_sha256=sha256_bytes(body[:ERROR_PREFIX_BYTES]))
                record["attempts"].append(attempt_record)
                record.update(details)
                # A schema error or a permanent HTTP error cannot be fixed by blind retries.
                if (isinstance(exc, SourceError) and not exc.retryable or isinstance(exc, ValueError)
                        or isinstance(exc, HTTPError) and exc.code not in TRANSIENT_HTTP):
                    break
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 4))
        record.update(status="failed", error=last_error, completed_at=utc_now())
        if isinstance(last_exception, SourceMaintenanceError):
            last_attempt = record["attempts"][-1]
            self.maintenance = {"notice": last_attempt["maintenance_notice"], "url": url}
            record.update(maintenance=True, maintenance_notice=last_attempt["maintenance_notice"], maintenance_source_url=url,
                          maintenance_body_prefix_sha256=last_attempt["maintenance_body_prefix_sha256"])
            raise SourceMaintenanceError(f"Request exhausted its retries and still returned a current maintenance notice at {url}: " + last_attempt["maintenance_notice"]) from None
        temporary = (isinstance(last_exception, HTTPError) and last_exception.code in TRANSIENT_HTTP
                     or isinstance(last_exception, (URLError, HTTPException, TimeoutError, OSError)) and not isinstance(last_exception, HTTPError))
        error_type = SourceUnavailableError if temporary else SourceError
        raise error_type(f"Failed to retrieve {url}: {last_error}") from None

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
