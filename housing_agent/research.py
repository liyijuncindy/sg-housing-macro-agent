"""Calendar-aligned exploratory research on saved housing and candidate data.

This module makes no network/model calls and does not change indicator selection.
Historical vintages and publication-time availability are not reconstructed.
"""
from __future__ import annotations

from datetime import date
import math

from .engine import _iso_date, _period_details, _period_from_ordinal


LAGS = (0, 1, 2, 4)
MIN_TRAINING = 24
MIN_HOLDOUT = 8
MIN_CORRELATION = 8
ANALYSIS_START_YEAR = 2015
ANALYSIS_START_QUARTER = ANALYSIS_START_YEAR * 4
RIDGE_PENALTY = 1.0
VACANCY_IDS = ("M400841:2", "M400841:1")
OUTCOME_NAMES = {
    "M212261:1": "Private residential property price index",
    "M212311:1": "Private residential rental index",
    "M212161:1": "HDB resale price index",
}
_FEATURES = {
    "percent": ("%", "Year-on-year percentage change, using the exact prior-year calendar period."),
    "percentage_point": ("percentage points", "Year-on-year level difference in percentage points, using the exact prior-year calendar period."),
    "basis_point": ("basis points", "Year-on-year rate difference multiplied by one hundred, using the exact prior-year calendar period."),
}


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _round(value):
    return round(value, 10) + 0.0


def _index(evaluations, label):
    if not isinstance(evaluations, list):
        raise ValueError(f"{label} must be a list")
    result = {}
    for item in evaluations:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in result:
            raise ValueError(f"{label} must contain unique nonempty IDs")
        result[item["id"]] = item
    return result


def _history(evaluation, cutoff):
    """Recheck calendar/finite-value constraints rather than trust positional rows."""
    meta = evaluation.get("metadata", {})
    frequency = meta.get("frequency")
    if frequency not in {"A", "Q", "M"}:
        raise ValueError("Missing or unsupported observation frequency")
    observations = evaluation.get("observations")
    if not isinstance(observations, list):
        raise ValueError("Missing observation history")
    history, seen = {}, set()
    for obs in observations:
        if not isinstance(obs, dict):
            raise ValueError("Observation must be an object")
        ordinal, start, end = _period_details(obs.get("period"), frequency)
        if ordinal in seen:
            raise ValueError("Duplicate calendar period in observation history")
        seen.add(ordinal)
        reference = _iso_date(obs["observation_date"], "observation_date") if obs.get("observation_date") else end
        if not start <= reference <= end:
            raise ValueError("Observation reference date is outside its calendar period")
        if reference > cutoff or (obs.get("published_at") and _iso_date(obs["published_at"], "published_at") > cutoff):
            continue
        value = obs.get("value")
        if value is None:
            continue
        if not _finite(value):
            raise ValueError("Nonfinite or nonnumeric observation")
        history[ordinal] = {"period": obs["period"], "value": float(value), "observation_date": reference.isoformat()}
    return frequency, history


def _difference(current, base, kind):
    if kind == "percent":
        if base == 0:
            return None
        value = (current / base - 1) * 100
    elif kind == "basis_point":
        value = (current - base) * 100
    else:
        value = current - base
    return value if math.isfinite(value) else None


def _features(evaluation, cutoff):
    meta = evaluation.get("metadata", {})
    frequency, history = _history(evaluation, cutoff)
    first = ANALYSIS_START_YEAR * {"A": 1, "Q": 4, "M": 12}[frequency]
    history = {ordinal: obs for ordinal, obs in history.items() if ordinal >= first
               and (frequency == "A" or _period_details(obs["period"], frequency)[2] <= cutoff)}
    kind = meta.get("change_kind")
    if kind not in _FEATURES:
        raise ValueError("Unsupported feature change kind; no implicit normalization was applied")
    steps = {"A": 1, "Q": 4, "M": 12}[frequency]
    values, points = {}, []
    for ordinal in sorted(history):
        if ordinal - steps not in history:
            continue
        if frequency == "M" and (ordinal % 12 + 1) % 3:
            continue  # Only March/June/September/December, never adjacent substitutes.
        current, base = history[ordinal], history[ordinal - steps]
        value = _difference(current["value"], base["value"], kind)
        if value is None:
            continue
        aligned = (ordinal // 12) * 4 + (ordinal % 12) // 3 if frequency == "M" else ordinal
        period = _period_from_ordinal(aligned, "A" if frequency == "A" else "Q")
        values[aligned] = value
        points.append({"period": period, "value": _round(value), "source_period": current["period"],
                       "base_period": base["period"], "source_value": current["value"], "base_value": base["value"]})
    return frequency, values, points


def _quarterly_outcome(evaluation, cutoff):
    frequency, history = _history(evaluation, cutoff)
    if frequency != "Q":
        raise ValueError("Housing outcome must be a quarterly index; no interpolation was applied")
    history = {ordinal: obs for ordinal, obs in history.items() if _period_details(obs["period"], frequency)[2] <= cutoff}
    qoq, yoy, points = {}, {}, []
    for ordinal in sorted(history):
        current = history[ordinal]
        if current["value"] <= 0:
            continue
        for offset, target in ((1, qoq), (4, yoy)):
            base = history.get(ordinal - offset)
            if base is not None and base["value"] > 0:
                value = _difference(current["value"], base["value"], "percent")
                if value is not None:
                    target[ordinal] = value
        if ordinal in qoq:
            points.append({"period": current["period"], "value": _round(qoq[ordinal]), "unit": "%",
                           "index_value": current["value"], "previous_period": history[ordinal - 1]["period"],
                           "previous_value": history[ordinal - 1]["value"]})
    latest = history[max(history)] if history else None
    changes = []
    if latest:
        ordinal = max(history)
        for comparison, offset, values in (("previous_period", 1, qoq), ("year_on_year", 4, yoy)):
            base = history.get(ordinal - offset)
            changes.append({"comparison": comparison, "value": _round(values[ordinal]) if ordinal in values else None,
                            "unit": "%", "latest_period": latest["period"],
                            "base_period": _period_from_ordinal(ordinal - offset, "Q"),
                            "reason": None if ordinal in values else "Exact calendar baseline or positive index value unavailable.",
                            "evidence": [latest] + ([base] if base else [])})
    return history, qoq, {ordinal // 4: value for ordinal, value in yoy.items() if ordinal % 4 == 3}, points, latest, changes


def _correlation(features, targets, lag, annual):
    matched = [(origin, origin + lag, x, targets[origin + lag])
               for origin, x in sorted(features.items()) if origin + lag in targets]
    n = len(matched)
    frequency = "A" if annual else "Q"
    result = {"lag": lag, "lag_unit": "years" if annual else "quarters", "n": n, "pearson_r": None,
              "status": "skipped", "reason": None,
              "start_period": _period_from_ordinal(matched[0][1], frequency) if matched else None,
              "end_period": _period_from_ordinal(matched[-1][1], frequency) if matched else None}
    if n < MIN_CORRELATION:
        result["reason"] = "Fewer than eight exact-calendar matched observations; sparse history is not scored."
        return result
    xs, ys = [row[2] for row in matched], [row[3] for row in matched]
    try:
        xmean, ymean = math.fsum(xs) / n, math.fsum(ys) / n
        dx, dy = [x - xmean for x in xs], [y - ymean for y in ys]
        xx, yy = math.fsum(x * x for x in dx), math.fsum(y * y for y in dy)
        if xx <= 1e-24 or yy <= 1e-24:
            result["reason"] = "Correlation is undefined for a constant feature or outcome."
            return result
        r = math.fsum(x * y for x, y in zip(dx, dy)) / math.sqrt(xx) / math.sqrt(yy)
        if not math.isfinite(r):
            raise ArithmeticError("Nonfinite correlation")
    except (ArithmeticError, ValueError):
        result["reason"] = "Numerical range prevents a finite correlation."
        return result
    result.update(status="computed", reason=None, pearson_r=_round(max(-1.0, min(1.0, r))))
    return result


def _fit_ridge(training):
    n = len(training)
    mean_x = math.fsum(row["feature"] for row in training) / n
    mean_y = math.fsum(row["actual"] for row in training) / n
    scale = math.sqrt(math.fsum((row["feature"] - mean_x) ** 2 for row in training) / n)
    if scale <= 1e-12:
        return mean_x, 1.0, mean_y, 0.0, True
    z = [(row["feature"] - mean_x) / scale for row in training]
    coefficient = math.fsum(x * (row["actual"] - mean_y) for x, row in zip(z, training)) / (math.fsum(x * x for x in z) + RIDGE_PENALTY)
    return mean_x, scale, mean_y, coefficient, False


def _metrics(predictions, field):
    errors = [row[field] - row["actual"] for row in predictions]
    def sign(value):
        return 1 if value > 1e-12 else (-1 if value < -1e-12 else 0)
    n = len(errors)
    return {"n": n, "mae": _round(math.fsum(abs(error) for error in errors) / n),
            "rmse": _round(math.sqrt(math.fsum(error * error for error in errors) / n)),
            "directional_accuracy": _round(sum(sign(row[field]) == sign(row["actual"]) for row in predictions) / n)}


def _skipped_forecast(reason, n=0):
    return {"status": "skipped", "reason": reason, "min_training": MIN_TRAINING, "min_holdout": MIN_HOLDOUT,
            "available_pairs": n, "n_predictions": 0, "metrics": {}, "predictions": [],
            "holdout_start_period": None, "holdout_end_period": None}


def _walk_forward(features, targets):
    # All methods are scored on exactly these dates, including the last-change
    # baseline's requirement for an observed change at the forecast origin.
    pairs = [{"origin": origin, "target": origin + 1, "feature": value,
              "actual": targets[origin + 1], "last_change": targets[origin]}
             for origin, value in sorted(features.items()) if origin in targets and origin + 1 in targets]
    if len(pairs) < MIN_TRAINING + MIN_HOLDOUT:
        return _skipped_forecast("Insufficient history for at least twenty-four training pairs and eight subsequent holdout predictions; no annual interpolation or synthetic periods added.", len(pairs))
    predictions = []
    try:
        for index in range(MIN_TRAINING, len(pairs)):
            row, training = pairs[index], pairs[:index]
            # Training outcomes must have completed no later than this origin.
            if any(item["target"] > row["origin"] for item in training):
                raise ValueError("A future training outcome crossed the forecast origin")
            mean, scale, intercept, coefficient, constant = _fit_ridge(training)
            predicted = intercept + coefficient * (row["feature"] - mean) / scale
            if not all(math.isfinite(x) for x in (predicted, mean, scale, intercept, coefficient)):
                raise ArithmeticError("Nonfinite fitted prediction")
            predictions.append({"origin_period": _period_from_ordinal(row["origin"], "Q"),
                "target_period": _period_from_ordinal(row["target"], "Q"), "actual": row["actual"],
                "feature": row["feature"], "ridge": predicted, "historical_mean": intercept,
                "last_change": row["last_change"], "zero_change": 0.0, "training_count": len(training),
                "training_target_start": _period_from_ordinal(training[0]["target"], "Q"),
                "training_target_end": _period_from_ordinal(training[-1]["target"], "Q"),
                "training_feature_mean": mean, "training_feature_scale": scale,
                "coefficient_standardized": coefficient, "intercept": intercept, "constant_training_feature": constant})
        metrics = {name: _metrics(predictions, name) for name in ("ridge", "historical_mean", "last_change", "zero_change")}
    except (ArithmeticError, ValueError):
        return _skipped_forecast("Numerical range or chronological validation prevented a reliable walk-forward fit; no partial score reported.", len(pairs))
    return {"status": "evaluated", "reason": None, "min_training": MIN_TRAINING, "min_holdout": MIN_HOLDOUT,
            "available_pairs": len(pairs), "n_predictions": len(predictions), "metrics": metrics,
            "holdout_start_period": predictions[0]["target_period"], "holdout_end_period": predictions[-1]["target_period"],
            "predictions": predictions}


def _vacancy_rate(by_id, cutoff):
    result = {"id": "derived_private_vacancy_rate", "name": "Derived completed private residential vacancy rate",
              "status": "skipped", "reason": None, "source_ids": list(VACANCY_IDS), "unit": "%",
              "formula": "vacant completed private units / matching completed private residential stock * 100",
              "latest": None, "changes": [], "observations": [], "excluded_invalid_pairs": 0}
    if any(key not in by_id for key in VACANCY_IDS):
        result["reason"] = "Both matching private-vacancy count and completed-stock histories are required."
        return result
    try:
        frequency_v, vacant = _history(by_id[VACANCY_IDS[0]], cutoff)
        frequency_s, stock = _history(by_id[VACANCY_IDS[1]], cutoff)
        if frequency_v != "Q" or frequency_s != "Q":
            raise ValueError("Vacancy numerator and stock denominator must both be quarterly")
        if by_id[VACANCY_IDS[0]]["metadata"].get("unit") != by_id[VACANCY_IDS[1]]["metadata"].get("unit"):
            raise ValueError("Vacancy numerator and stock denominator units do not match")
    except (ValueError, TypeError, KeyError) as exc:
        result["reason"] = str(exc)
        return result
    rates = {}
    for ordinal in sorted(set(vacant) & set(stock)):
        numerator, denominator = vacant[ordinal]["value"], stock[ordinal]["value"]
        if denominator <= 0 or not 0 <= numerator <= denominator:
            result["excluded_invalid_pairs"] += 1
            continue
        value = numerator / denominator * 100
        row = {"period": vacant[ordinal]["period"], "value": _round(value), "unit": "%",
               "vacant_units": numerator, "total_units": denominator,
               "evidence": [{"series_id": VACANCY_IDS[0], **vacant[ordinal]}, {"series_id": VACANCY_IDS[1], **stock[ordinal]}]}
        rates[ordinal] = row
        result["observations"].append(row)
    if not rates:
        result["reason"] = "No valid exact-quarter numerator/denominator pair was available."
        return result
    ordinal = max(rates)
    result.update(status="computed", latest=rates[ordinal])
    for name, offset in (("previous_period", 1), ("year_on_year", 4)):
        base = rates.get(ordinal - offset)
        result["changes"].append({"comparison": name, "value": _round(rates[ordinal]["value"] - base["value"]) if base else None,
                                  "unit": "percentage points", "latest_period": rates[ordinal]["period"],
                                  "base_period": _period_from_ordinal(ordinal - offset, "Q"),
                                  "reason": None if base else "Matching prior calendar-quarter rate unavailable.",
                                  "evidence": [rates[ordinal]] + ([base] if base else [])})
    return result


def build_research(evaluations: list[dict], outcomes: list[dict], as_of: str) -> dict:
    """Return every candidate/outcome comparison without ranking or reselection."""
    cutoff = _iso_date(as_of, "as_of")
    by_id, outcome_ids = _index(evaluations, "evaluations"), _index(outcomes, "outcomes")
    result = {"schema_version": 1, "as_of": as_of, "candidates": [], "outcomes": [], "comparisons": [],
        "methodology": {
            "purpose": "Exploratory associations and retrospective walk-forward validation, not confirmed forward forecasting ability.",
            "analysis_start_period": "2015-Q1",
            "methodology_threshold": "Private residential index methodology changed in 2015-Q1 and HDB resale methodology in 2014-Q4. All statistical feature and outcome changes require both current and base observations from 2015-Q1 onward (annual observations from 2015 onward); earlier captures remain available for audit and descriptive charts.",
            "target": "Next-quarter quarter-on-quarter percentage change in a housing price or rent index; not a currency price or return on a property.",
            "monthly_alignment": "Use only actual March, June, September and December observations and their exact prior-year month; no averaging, interpolation or nearest-month substitution.",
            "annual_analysis": "Separate annual feature changes versus same-year Q4 outcome year-on-year changes; lags are years. No quarterly forecast or interpolation for annual candidates.",
            "correlations": "Pearson correlation at predeclared lags zero, one, two and four. Positive lag means candidate leads outcome. Constant or fewer than eight matched values are unscored.",
            "min_correlation_pairs": MIN_CORRELATION,
            "forecast": "Fixed one-quarter lead; expanding-window univariate ridge with an unpenalized intercept. Feature mean and population standard deviation are fitted on training pairs only.",
            "ridge_penalty": RIDGE_PENALTY, "min_training": MIN_TRAINING, "min_holdout": MIN_HOLDOUT,
            "baselines": "Expanding historical mean of training targets, latest observed quarter-on-quarter change at forecast origin, and zero/no-change. All methods use identical holdout dates.",
            "directional_accuracy": "Fraction from zero to one matching positive, negative or zero actual change; absolute values within one trillionth are treated as zero.",
            "metric_unit": "Percentage points of index percentage change for MAE and RMSE.",
        },
        "caveats": [
            "Latest-vintage historical analysis: revisions and historical publication availability are not reconstructed. Observation-period alignment does not prove that features were known at the forecast origin.",
            "No causal claim, production forecast, property-price estimate or validated investment signal is established. These indices describe aggregate markets.",
            "All configured candidate/outcome comparisons are retained, including skipped results. Lags and the ridge penalty were not selected by holdout performance; no best model is promoted.",
            "The same histories support many exploratory comparisons. Correlations have no multiple-testing adjustment or significance claim, and the holdout has not been reserved for a later untouched confirmatory test.",
            "Annual results use a different outcome horizon from quarterly results and must not be compared as if they were the same experiment.",
            "Current candidate eligibility is a data-usability screen, not evidence of historical or future predictive value.",
        ]}
    prepared_outcomes = {}
    for key, evaluation in outcome_ids.items():
        meta = evaluation.get("metadata", {})
        card = {"id": key, "name": OUTCOME_NAMES.get(key, meta.get("name", key)),
                "official_row_name": meta.get("name", key), "unit": meta.get("unit"),
                "source_url": meta.get("source_url"), "source_agency": meta.get("source_agency"),
                "status": "unavailable", "reason": None, "latest": None, "changes": [], "quarterly_changes": []}
        try:
            history, qoq, annual, points, latest, changes = _quarterly_outcome(evaluation, cutoff)
            if not evaluation.get("quality", {}).get("eligible"):
                raise ValueError("Outcome did not pass the saved data-quality gate")
            if not qoq:
                raise ValueError("No exact-quarter outcome changes are available")
            prepared_outcomes[key] = ({period: value for period, value in qoq.items() if period - 1 >= ANALYSIS_START_QUARTER},
                                      {year: value for year, value in annual.items() if year - 1 >= ANALYSIS_START_YEAR})
            card.update(status="available", latest=latest, changes=changes, quarterly_changes=points)
        except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
            card["reason"] = str(exc)
        result["outcomes"].append(card)
    for key, evaluation in by_id.items():
        meta = evaluation.get("metadata", {})
        kind = meta.get("change_kind")
        unit, definition = _FEATURES.get(kind, (None, "No supported feature normalization available."))
        card = {"id": key, "name": meta.get("name", key), "frequency": meta.get("frequency"),
                "feature_unit": unit, "feature_definition": definition, "status": "unavailable", "reason": None,
                "feature_observations": []}
        features, frequency = {}, meta.get("frequency")
        try:
            frequency, features, points = _features(evaluation, cutoff)
            if not evaluation.get("quality", {}).get("eligible"):
                raise ValueError("Candidate did not pass the saved data-quality gate")
            if not features:
                raise ValueError("No valid exact-year changes at the required calendar frequency")
            card.update(status="available", feature_observations=points)
        except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
            card["reason"] = str(exc)
        result["candidates"].append(card)
        annual = frequency == "A"
        for outcome in result["outcomes"]:
            unavailable = card["reason"] or outcome["reason"]
            target = prepared_outcomes.get(outcome["id"], ({}, {}))[1 if annual else 0]
            correlations = [_correlation(features if not unavailable else {}, target, lag, annual) for lag in LAGS]
            if unavailable:
                for row in correlations:
                    row["reason"] = unavailable
                forecast = _skipped_forecast(unavailable)
            elif annual:
                forecast = _skipped_forecast("Annual candidate: quarterly interpolation was not performed; annual associations are reported separately.")
            else:
                forecast = _walk_forward(features, target)
            result["comparisons"].append({"candidate_id": key, "outcome_id": outcome["id"],
                "analysis_frequency": "annual" if annual else "quarterly",
                "target_change": "Q4 year-on-year index percentage change" if annual else "Quarter-on-quarter index percentage change",
                "correlations": correlations, "walk_forward": forecast})
    result["derived_private_vacancy_rate"] = _vacancy_rate(by_id, cutoff)
    scored = sum(item["walk_forward"]["status"] == "evaluated" for item in result["comparisons"])
    result["summary"] = {"candidate_count": len(by_id), "outcome_count": len(outcome_ids),
                         "comparison_count": len(result["comparisons"]), "forecast_evaluated": scored,
                         "forecast_skipped": len(result["comparisons"]) - scored}
    return result
