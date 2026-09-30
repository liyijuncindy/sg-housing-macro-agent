"""Deterministic, auditable data checks and candidate selection.

Quality scores measure usability of the captured data. They are neither forecasts
nor evidence of a relationship with housing prices. Calendar periods, rather than
row positions, determine every comparison.
"""

from __future__ import annotations

import calendar
from copy import deepcopy
from datetime import date
import math
import re
from typing import Any


_RULES = {
    "A": {"minimum_valid": 3, "maximum_lag": 2, "annual_steps": 1},
    "Q": {"minimum_valid": 8, "maximum_lag": 3, "annual_steps": 4},
    "M": {"minimum_valid": 24, "maximum_lag": 6, "annual_steps": 12},
}
_MINIMUM_COMPLETENESS = 0.75
_CHANGE_KINDS = {"percent", "percentage_point", "basis_point", "absolute"}
_VINTAGE_WARNING = (
    "Latest-vintage snapshot: period/reference-date filtering does not establish "
    "what was historically available or exclude later revisions. Known publication "
    "dates are respected; unknown publication dates are not inferred."
)


def _iso_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError(f"{label} must be an ISO date (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not a valid calendar date: {value!r}") from exc


def _period_details(period: Any, frequency: str) -> tuple[int, date, date]:
    """Return a contiguous period ordinal, start date and end date."""
    patterns = {"A": r"(\d{4})", "Q": r"(\d{4})-Q([1-4])", "M": r"(\d{4})-(0[1-9]|1[0-2])"}
    match = re.fullmatch(patterns[frequency], period) if isinstance(period, str) else None
    if match is None:
        raise ValueError(f"Period {period!r} does not match frequency {frequency}")
    year = int(match.group(1))
    if not 1 <= year <= 9999:
        raise ValueError(f"Period year must be between 0001 and 9999: {period!r}")
    if frequency == "A":
        return year, date(year, 1, 1), date(year, 12, 31)
    number = int(match.group(2))
    if frequency == "Q":
        first_month = 3 * number - 2
        last_month = first_month + 2
        return year * 4 + number - 1, date(year, first_month, 1), date(year, last_month, calendar.monthrange(year, last_month)[1])
    return year * 12 + number - 1, date(year, number, 1), date(year, number, calendar.monthrange(year, number)[1])


def _period_from_ordinal(ordinal: int, frequency: str) -> str | None:
    if frequency == "A":
        return f"{ordinal:04d}" if 1 <= ordinal <= 9999 else None
    divisor = 4 if frequency == "Q" else 12
    year, zero_based = divmod(ordinal, divisor)
    if not 1 <= year <= 9999:
        return None
    return f"{year:04d}-Q{zero_based + 1}" if frequency == "Q" else f"{year:04d}-{zero_based + 1:02d}"


def _last_completed_ordinal(as_of: date, frequency: str) -> int:
    if frequency == "A":
        return as_of.year if as_of.month == 12 and as_of.day == 31 else as_of.year - 1
    if frequency == "Q":
        quarter = (as_of.month - 1) // 3 + 1
        period = f"{as_of.year:04d}-Q{quarter}"
    else:
        period = f"{as_of.year:04d}-{as_of.month:02d}"
    ordinal, _, end = _period_details(period, frequency)
    return ordinal if as_of == end else ordinal - 1


def _change(series: dict, latest: dict | None, by_period: dict, comparison: str) -> dict:
    frequency = series["frequency"]
    kind = series["change_kind"]
    units = {"percent": "%", "percentage_point": "percentage points", "basis_point": "basis points", "absolute": series["unit"]}
    formulas = {
        "percent": "(latest_value / base_value - 1) * 100",
        "percentage_point": "latest_value - base_value",
        "basis_point": "(latest_value - base_value) * 100",
        "absolute": "latest_value - base_value",
    }
    result = {
        "id": f"{series['id']}:{comparison}", "comparison": comparison,
        "value": None, "unit": units[kind], "latest_period": None,
        "latest_value": None, "base_period": None, "base_value": None,
        "formula": formulas[kind], "reason": None, "evidence": [],
    }
    if latest is None:
        result["reason"] = "No valid observation is available within the report cutoff."
        return result
    result.update(latest_period=latest["period"], latest_value=latest["value"])
    result["evidence"].append(deepcopy(latest))
    ordinal, _, _ = _period_details(latest["period"], frequency)
    offset = 1 if comparison == "previous_period" else _RULES[frequency]["annual_steps"]
    base_period = _period_from_ordinal(ordinal - offset, frequency)
    result["base_period"] = base_period
    base = by_period.get(base_period)
    if base is None:
        result["reason"] = f"Calendar baseline {base_period or '(outside supported calendar)'} is absent or outside the cutoff; no adjacent row was substituted."
        return result
    result["evidence"].append(deepcopy(base))
    result["base_value"] = base["value"]
    if base["value"] is None:
        result["reason"] = f"Calendar baseline {base_period} has a missing value."
        return result
    if kind == "percent" and base["value"] == 0:
        result["reason"] = f"Calendar baseline {base_period} is zero; percentage change is undefined."
        return result
    try:
        if kind == "percent":
            value = (latest["value"] / base["value"] - 1) * 100
        elif kind == "basis_point":
            value = (latest["value"] - base["value"]) * 100
        else:
            value = latest["value"] - base["value"]
        finite = math.isfinite(value)
    except (OverflowError, ZeroDivisionError):
        finite = False
    if not finite:
        result["reason"] = "The calculation exceeds finite numeric range."
        return result
    # Suppress binary float noise without changing the evidence values.
    result["value"] = round(value, 10) + 0.0
    return result


def evaluate_series(series: dict, as_of: str) -> dict:
    """Validate one normalized series, apply the cutoff and calculate its quality.

    The default cutoff is the end of the period. A source-backed observation_date
    can identify a point-in-time observation within that same period. The source
    adapter, not this module, must establish the provenance of that override.
    """
    cutoff = _iso_date(as_of, "as_of")
    if not isinstance(series, dict):
        raise ValueError("series must be a dictionary")
    for key in ("id", "unit"):
        if not isinstance(series.get(key), str) or not series[key].strip():
            raise ValueError(f"series.{key} must be a nonempty string")
    frequency = series.get("frequency")
    if not isinstance(frequency, str) or frequency not in _RULES:
        raise ValueError(f"Unsupported frequency: {frequency!r}; expected A, Q or M")
    kind = series.get("change_kind")
    if not isinstance(kind, str) or kind not in _CHANGE_KINDS:
        raise ValueError(f"Unsupported change_kind: {kind!r}")
    allowed_comparisons = ["year_on_year"] if frequency == "A" else ["previous_period", "year_on_year"]
    comparisons = series.get("comparisons", allowed_comparisons)
    if (
        not isinstance(comparisons, list) or not comparisons
        or any(not isinstance(item, str) or item not in allowed_comparisons for item in comparisons)
        or len(comparisons) != len(set(comparisons))
    ):
        raise ValueError(f"comparisons must be a nonempty list of distinct values drawn from {allowed_comparisons}")
    if kind in {"basis_point", "percentage_point"}:
        unit = series["unit"].lower()
        if not re.search(r"%|percent|per\s+cent", unit) or "point" in unit:
            raise ValueError("Rate changes require levels stored in percentage units, not fractions, basis points or an unrelated unit")
    observations = series.get("observations")
    if not isinstance(observations, list):
        raise ValueError("series.observations must be a list")

    retained = []
    seen = set()
    excluded_period = excluded_publication = reference_overrides = 0
    for index, original in enumerate(observations):
        if not isinstance(original, dict) or "period" not in original or "value" not in original:
            raise ValueError(f"Observation {index} must contain period and value")
        observation = deepcopy(original)
        period = observation["period"]
        ordinal, start, end = _period_details(period, frequency)
        if period in seen:
            raise ValueError(f"Duplicate period {period!r} in series {series['id']}")
        seen.add(period)
        value = observation["value"]
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"Observation {period} value must be a finite number or null")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f"Observation {period} has a non-finite numeric value")
        reference_date = end
        if observation.get("observation_date") is not None:
            reference_date = _iso_date(observation["observation_date"], f"Observation {period} observation_date")
            if not start <= reference_date <= end:
                raise ValueError(f"Observation {period} observation_date must lie within its calendar period")
        published_at = None
        if observation.get("published_at") is not None:
            published_at = _iso_date(observation["published_at"], f"Observation {period} published_at")
        if reference_date > cutoff:
            excluded_period += 1
            continue
        if published_at is not None and published_at > cutoff:
            excluded_publication += 1
            continue
        if reference_date != end:
            reference_overrides += 1
        retained.append((ordinal, observation))
    retained.sort(key=lambda item: item[0])
    canonical = [item[1] for item in retained]
    valid = [(ordinal, observation) for ordinal, observation in retained if observation["value"] is not None]
    latest = deepcopy(valid[-1][1]) if valid else None
    by_period = {observation["period"]: observation for observation in canonical}
    changes = [_change(series, latest, by_period, comparison) for comparison in comparisons]

    rules = _RULES[frequency]
    # Assess usability over recent history so sparse early archival observations
    # do not disqualify a complete modern series. A shorter series can qualify
    # under the separately disclosed minimum-history threshold.
    window_end = max(_last_completed_ordinal(cutoff, frequency), retained[-1][0] if retained else 0)
    minimum_ordinal = {"A": 1, "Q": 4, "M": 12}[frequency]
    window_start = max(minimum_ordinal, window_end - 10 * rules["annual_steps"] + 1)
    window_retained = [(ordinal, observation) for ordinal, observation in retained if ordinal >= window_start]
    window_valid = [(ordinal, observation) for ordinal, observation in valid if ordinal >= window_start]
    valid_count = len(window_valid)
    expected_count = window_retained[-1][0] - window_retained[0][0] + 1 if window_retained else 0
    missing_count = expected_count - valid_count
    missing_fraction = missing_count / expected_count if expected_count else 1.0
    completeness = 1.0 - missing_fraction
    lag = max(0, _last_completed_ordinal(cutoff, frequency) - valid[-1][0]) if valid else None
    reasons = []
    warnings = [_VINTAGE_WARNING]
    if valid_count < rules["minimum_valid"]:
        reasons.append(f"Insufficient history: {valid_count} valid {frequency} observations; at least {rules['minimum_valid']} are required.")
    if completeness < _MINIMUM_COMPLETENESS:
        reasons.append(f"Incomplete history: {completeness:.1%} of calendar periods have values; at least {_MINIMUM_COMPLETENESS:.0%} are required.")
    if lag is None:
        reasons.append("No usable observation exists within the report cutoff.")
    elif lag > rules["maximum_lag"]:
        reasons.append(f"Stale data: latest value is {lag} completed {frequency} periods behind the cutoff; at most {rules['maximum_lag']} are allowed.")
    if missing_count:
        warnings.append(f"{missing_count} calendar periods are missing or null between the first and last retained observations in the quality window.")
    if len(window_retained) < len(retained):
        warnings.append("Quality history and completeness use only the most recent ten calendar years; older observations remain available for audit and calendar comparisons.")
    if canonical and canonical[-1]["value"] is None:
        warnings.append("The most recent retained period has no value; latest refers to the most recent finite value.")
    if excluded_period:
        warnings.append(f"Excluded {excluded_period} observations whose period end or source-backed reference date is after the cutoff.")
    if excluded_publication:
        warnings.append(f"Excluded {excluded_publication} observations with a known publication date after the cutoff.")
    if reference_overrides:
        warnings.append(f"Used source-backed observation dates within the period for {reference_overrides} observations; other observations use period-end cutoffs.")
    for change in changes:
        if change["reason"]:
            warnings.append(f"{change['comparison']}: {change['reason']}")
        elif kind == "percent" and change["base_value"] < 0:
            warnings.append(f"{change['comparison']}: percent change uses a negative signed denominator; interpret the result with care.")
    components = {
        "history": 30.0 * min(1.0, valid_count / (2 * rules["minimum_valid"])),
        "completeness": 35.0 * completeness,
        "recency": 20.0 * max(0.0, 1.0 - lag / (rules["maximum_lag"] + 1)) if lag is not None else 0.0,
        "comparisons": 15.0 * sum(change["value"] is not None for change in changes) / len(changes),
    }
    # Empty histories should not receive quality credit from an empty denominator.
    score = round(sum(components.values()), 2)
    quality = {
        "eligible": not reasons, "score": score, "reasons": reasons,
        "warnings": warnings, "missing_fraction": missing_fraction,
        "valid_count": valid_count, "expected_count": expected_count,
        "window_valid_count": valid_count, "total_valid_count": len(valid),
        "window_start_period": _period_from_ordinal(window_start, frequency),
        "window_end_period": _period_from_ordinal(window_end, frequency),
        "coverage_start_period": window_retained[0][1]["period"] if window_retained else None,
        "coverage_end_period": window_retained[-1][1]["period"] if window_retained else None,
        "missing_count": missing_count, "lag_periods": lag,
        "thresholds": {"minimum_valid": rules["minimum_valid"], "minimum_completeness": _MINIMUM_COMPLETENESS, "maximum_lag_periods": rules["maximum_lag"]},
        "score_components": {key: round(value, 4) for key, value in components.items()},
        "score_definition": "Data usability only (0–100): history 30, completeness 35, recency 20, computable permitted comparisons 15. History and completeness use the most recent ten calendar years. Completeness spans the first through last retained period in that window; missing recent releases are assessed separately through recency. History saturates at twice the minimum valid count. Not predictive validation.",
    }
    return {"id": series["id"], "metadata": deepcopy({key: value for key, value in series.items() if key != "observations"}), "latest": latest, "changes": changes, "quality": quality, "observations": canonical}


def select_candidates(evaluations: list[dict], limit: int = 5) -> dict:
    """Choose eligible candidates by usability, first covering economic families."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a nonnegative integer")
    if not isinstance(evaluations, list):
        raise ValueError("evaluations must be a list")
    seen = set()
    for evaluation in evaluations:
        if not isinstance(evaluation, dict) or not isinstance(evaluation.get("id"), str) or not evaluation["id"].strip():
            raise ValueError("Each evaluation must contain a nonempty string id")
        if evaluation["id"] in seen:
            raise ValueError(f"Duplicate candidate id {evaluation['id']!r}")
        seen.add(evaluation["id"])
        quality = evaluation.get("quality")
        if not isinstance(quality, dict) or not isinstance(quality.get("eligible"), bool):
            raise ValueError(f"Candidate {evaluation['id']} requires a boolean quality.eligible")
        score = quality.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100 or not math.isfinite(score):
            raise ValueError(f"Candidate {evaluation['id']} requires a finite quality score from 0 to 100")
        if not isinstance(evaluation.get("metadata"), dict):
            raise ValueError(f"Candidate {evaluation['id']} requires metadata")
        if not isinstance(quality.get("reasons", []), list):
            raise ValueError(f"Candidate {evaluation['id']} quality.reasons must be a list")

    def family(item: dict) -> str:
        raw = item["metadata"].get("selection_family")
        if not isinstance(raw, str) or not raw.strip():
            raw = item["metadata"].get("theme")
        return raw.strip().casefold() if isinstance(raw, str) and raw.strip() else "unspecified"

    eligible = sorted((item for item in evaluations if item["quality"]["eligible"]), key=lambda item: (-item["quality"]["score"], item["id"]))
    selected_ids = []
    represented = set()
    selection_reasons = {}
    for item in eligible:
        if len(selected_ids) >= limit:
            break
        if family(item) not in represented:
            selected_ids.append(item["id"])
            represented.add(family(item))
            selection_reasons[item["id"]] = f"Selected for economic-family coverage ({family(item)}): highest data-quality score within this family, with deterministic id tie-breaking. The family defaults to the theme when not specified."
    for item in eligible:
        if len(selected_ids) >= limit:
            break
        if item["id"] not in selection_reasons:
            selected_ids.append(item["id"])
            selection_reasons[item["id"]] = f"Selected to fill remaining capacity by data-quality score after economic-family coverage; family: {family(item)}."
    decisions = []
    for item in sorted(evaluations, key=lambda candidate: candidate["id"]):
        selected = item["id"] in selection_reasons
        if selected:
            reason = selection_reasons[item["id"]]
        elif not item["quality"]["eligible"]:
            reasons = item["quality"].get("reasons", [])
            reason = "Excluded by data-quality rules: " + ("; ".join(str(value) for value in reasons) if reasons else "candidate is ineligible")
        else:
            reason = f"Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: {family(item)}."
        decisions.append({"id": item["id"], "selected": selected, "reason": reason})
    return {
        "selected_ids": selected_ids, "decisions": decisions,
        "method": "Deterministic data-quality and economic-family diversity selection. Family is metadata.selection_family when specified, otherwise metadata.theme. Exclude ineligible data; sort by quality score descending then id ascending; first select the best candidate per family, then fill remaining capacity by score. Never fill capacity with ineligible data. Scores measure usability and do not establish causal or predictive value; no target-based predictive validation is performed.",
    }
