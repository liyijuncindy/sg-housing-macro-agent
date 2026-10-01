"""Audited public-file transport shared by independent MOM and MAS adapters."""
from __future__ import annotations

from http.cookiejar import CookieJar
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPCookieProcessor, Request, build_opener

from .sources import SourceError, _response_details
from .storage import sha256_bytes, utc_now, write_json

ALLOWED_HOSTS = {"stats.mom.gov.sg", "eservices.mas.gov.sg"}
MAX_BYTES = 20 * 1024 * 1024
DIRECT_IDS = {"M182342:2", "M184101:1", "M700071:23"}


def _validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username or parsed.password or parsed.port not in (None, 443)):
        raise SourceError("Independent downloads require an approved public MOM or MAS HTTPS URL")


class _OfficialRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class OfficialFileClient:
    def __init__(self, run_dir: Path, timeout: float = 20, retries: int = 2):
        self.run_dir = run_dir
        self.timeout = timeout
        self.retries = retries
        self.records: list[dict] = []
        self.opener = build_opener(_OfficialRedirects(), HTTPCookieProcessor(CookieJar()))

    def download(self, url: str, *, name: str, suffix: str, data: bytes | None = None,
                 headers: dict | None = None) -> tuple[bytes, dict]:
        _validate_url(url)
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name) or not re.fullmatch(r"\.[a-z0-9]+", suffix):
            raise SourceError("Invalid raw artifact name")
        if data is not None and not isinstance(data, bytes):
            raise SourceError("Download form data must be bytes")
        request_headers = {"User-Agent": "HousingResearchAgent/0.1 (public statistical research)",
                           "Accept": "*/*"}
        if headers:
            if any(key.lower() not in {"accept", "content-type", "referer"} for key in headers):
                raise SourceError("Only public download headers are supported")
            request_headers.update(headers)
        record = {"url": url, "method": "POST" if data is not None else "GET",
                  "retrieved_at": utc_now(), "attempts": [], "status": "pending"}
        if data is not None:
            record["request_body_sha256"] = sha256_bytes(data)
        self.records.append(record)
        token = sha256_bytes(url.encode() + b"\0" + (data or b""))[:16]
        raw_path = self.run_dir / "raw" / f"{name}_{len(self.records):02d}_{token}{suffix}"
        last_error = None
        for attempt in range(self.retries + 1):
            details = {}
            try:
                req = Request(url, data=data, headers=request_headers)
                with self.opener.open(req, timeout=self.timeout) as response:
                    final_url = response.geturl()
                    _validate_url(final_url)
                    details = _response_details(getattr(response, "status", 200), response.headers)
                    details["final_url"] = final_url
                    modified = response.headers.get("Last-Modified")
                    if modified:
                        details["http_last_modified"] = modified[:1024]
                    record.update(details)
                    if details["http_status"] != 200:
                        raise SourceError(f"Expected a complete HTTP 200 file, got {details['http_status']}")
                    body = response.read(MAX_BYTES + 1)
                    if len(body) > MAX_BYTES:
                        raise SourceError("Response exceeds the download size limit")
                    if not body:
                        raise SourceError("Official download is empty")
                # Save original bytes before parsing so format changes remain auditable.
                raw_path.parent.mkdir(parents=True, exist_ok=True)
                raw_path.write_bytes(body)
                record.update(status="ok", completed_at=utc_now(),
                              raw_file=str(raw_path.relative_to(self.run_dir)), raw_sha256=sha256_bytes(body))
                record["attempts"].append({"attempt": attempt + 1, "status": "ok", **details})
                return body, record
            except (HTTPError, URLError, TimeoutError, OSError, ValueError, SourceError) as exc:
                if isinstance(exc, HTTPError):
                    details = _response_details(exc.code, exc.headers)
                    record.update(details)
                    exc.close()
                last_error = f"{type(exc).__name__}: {exc}"
                record["attempts"].append({"attempt": attempt + 1, "status": "failed", "error": last_error, **details})
                if (isinstance(exc, (ValueError, SourceError))
                        or isinstance(exc, HTTPError) and exc.code not in {408, 429, 500, 502, 503, 504}):
                    break
                if attempt < self.retries:
                    time.sleep(min(2 ** attempt, 4))
        record.update(status="failed", error=last_error, completed_at=utc_now())
        raise SourceError(f"Failed to retrieve {url}: {last_error}")

    def metadata(self, name: str, payload: dict) -> dict:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
            raise SourceError("Invalid metadata artifact name")
        path = self.run_dir / "raw" / f"{name}_adapter_metadata.json"
        if path.exists():
            raise SourceError("Adapter metadata cannot overwrite an existing artifact")
        write_json(path, {**payload, "metadata_origin": "Locally generated adapter metadata; not an official API response"})
        return {"raw_file": str(path.relative_to(self.run_dir)), "raw_sha256": sha256_bytes(path.read_bytes()),
                "retrieved_at": utc_now()}


def build_series(spec: dict, raw_record: dict, metadata_record: dict, observations: list[dict], **overrides) -> dict:
    """Keep the reviewed identity while explicitly recording the actual direct source."""
    table, row = spec["table_id"], str(spec["row_id"])
    series = {
        "id": f"{table}:{row}", "name": spec["expected_name"], "theme": spec["theme"],
        "selection_family": spec.get("selection_family", spec["theme"]),
        "definition": spec["definition"], "unit": spec["expected_unit"], "frequency": spec["frequency"],
        "update_frequency": spec["update_frequency"], "source_url": raw_record["url"],
        "api_url": raw_record["url"], "table_id": table, "row_id": row,
        "table_title": spec["expected_name"], "source_agency": "Not supplied",
        "source_provider": "Independent official download", "source_updated_at": None,
        "retrieved_at": raw_record["retrieved_at"], "source_footnote": "", "row_footnote": "",
        "change_kind": spec["change_kind"], "scope": spec.get("scope", "See source definition"),
        "seasonal_adjustment": spec.get("seasonal_adjustment", "Not established"),
        "reference_month_day": spec.get("reference_month_day"),
        **({"comparisons": spec["comparisons"]} if "comparisons" in spec else {}),
        "provenance": {"raw_file": raw_record["raw_file"], "raw_sha256": raw_record["raw_sha256"],
                       "metadata_file": metadata_record["raw_file"], "metadata_sha256": metadata_record["raw_sha256"]},
        "mechanism": spec["mechanism"], "availability_note": spec.get("availability_note", ""),
        "observations": observations,
    }
    series.update(overrides)
    return series
