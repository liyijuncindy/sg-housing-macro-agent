"""Behavioral checks for cutoff, arithmetic, eligibility and selection."""

from copy import deepcopy
import unittest

from housing_agent.engine import evaluate_series, select_candidates


def series(period_values=(), frequency="Q", **overrides):
    result = {
        "id": "example", "name": "Example indicator", "theme": "activity",
        "definition": "A synthetic series used only by unit tests.",
        "unit": "Index", "frequency": frequency, "change_kind": "percent",
        "source_url": "https://example.invalid/test-only",
        "observations": [
            {"period": period, "value": value, "raw_period": period,
             "raw_value": str(value), "raw_index": index}
            for index, (period, value) in enumerate(period_values)
        ],
    }
    result.update(overrides)
    return result


def change(evaluation, comparison="year_on_year"):
    return next(item for item in evaluation["changes"] if item["comparison"] == comparison)


def candidate(identifier, score, theme, eligible=True):
    return {"id": identifier, "metadata": {"theme": theme}, "quality": {
        "eligible": eligible, "score": score,
        "reasons": [] if eligible else ["Insufficient history"],
    }}


class CalendarArithmeticTests(unittest.TestCase):
    def test_missing_quarter_never_turns_positional_shift_into_year_on_year(self):
        # Removing Q3 shifts row positions, but must not move the calendar base.
        source = series([
            ("2022-Q4", 90), ("2023-Q1", 100), ("2023-Q2", 105),
            ("2023-Q4", 120), ("2024-Q1", 130),
        ])
        evaluation = evaluate_series(source, "2024-03-31")
        comparison = change(evaluation)
        wrong_positional_value = (source["observations"][-1]["value"] / source["observations"][-5]["value"] - 1) * 100
        self.assertAlmostEqual(wrong_positional_value, 44.44444444444444)
        self.assertEqual(comparison["value"], 30.0)
        self.assertEqual(comparison["base_period"], "2023-Q1")
        self.assertEqual(comparison["base_value"], 100)
        self.assertEqual([row["raw_index"] for row in comparison["evidence"]], [4, 1])
        self.assertIsNone(comparison["reason"])

    def test_missing_calendar_baseline_is_unavailable(self):
        evaluation = evaluate_series(series([
            ("2022-Q4", 90), ("2023-Q2", 100), ("2023-Q3", 110),
            ("2023-Q4", 120), ("2024-Q1", 130),
        ]), "2024-03-31")
        comparison = change(evaluation)
        self.assertEqual(comparison["base_period"], "2023-Q1")
        self.assertIsNone(comparison["value"])
        self.assertIn("no adjacent row", comparison["reason"])
        self.assertEqual(len(comparison["evidence"]), 1)

    def test_missing_previous_quarter_does_not_use_previous_available_row(self):
        evaluation = evaluate_series(series([("2023-Q4", 100), ("2024-Q4", 120)]), "2024-12-31")
        self.assertIsNone(change(evaluation, "previous_period")["value"])
        self.assertEqual(change(evaluation, "previous_period")["base_period"], "2024-Q3")
        self.assertEqual(change(evaluation)["value"], 20.0)

    def test_monthly_comparisons_cross_calendar_year(self):
        evaluation = evaluate_series(series([
            ("2023-01", 100), ("2023-12", 120), ("2024-01", 126),
        ], frequency="M"), "2024-01-31")
        self.assertEqual(change(evaluation)["value"], 26.0)
        previous = change(evaluation, "previous_period")
        self.assertEqual(previous["base_period"], "2023-12")
        self.assertEqual(previous["value"], 5.0)

    def test_annual_has_only_year_on_year(self):
        evaluation = evaluate_series(series([("2022", 100), ("2023", 110)], frequency="A"), "2023-12-31")
        self.assertEqual(len(evaluation["changes"]), 1)
        self.assertEqual(change(evaluation)["value"], 10.0)

    def test_source_can_request_only_year_on_year_for_nonseasonally_adjusted_data(self):
        source = series([("2023-Q1", 100), ("2023-Q4", 110), ("2024-Q1", 120)], comparisons=["year_on_year"], seasonal_adjustment="Not seasonally adjusted")
        evaluation = evaluate_series(source, "2024-03-31")
        self.assertEqual([item["comparison"] for item in evaluation["changes"]], ["year_on_year"])
        self.assertEqual(change(evaluation)["value"], 20)
        self.assertEqual(evaluation["quality"]["score_components"]["comparisons"], 15)

    def test_null_baseline_keeps_evidence_and_explanation(self):
        source = series([("2023-Q1", None), ("2024-Q1", 10)])
        comparison = change(evaluate_series(source, "2024-03-31"))
        self.assertIsNone(comparison["value"])
        self.assertIn("missing value", comparison["reason"])
        self.assertEqual(comparison["evidence"][1], source["observations"][0])

    def test_zero_baseline_only_blocks_percentage_calculation(self):
        source = series([("2022", 0), ("2023", 10)], frequency="A")
        percentage = change(evaluate_series(source, "2023-12-31"))
        self.assertIsNone(percentage["value"])
        self.assertIn("zero", percentage["reason"])
        source["change_kind"] = "absolute"
        absolute = change(evaluate_series(source, "2023-12-31"))
        self.assertEqual(absolute["value"], 10)
        self.assertEqual(absolute["unit"], "Index")

    def test_rate_changes_use_percentage_points_or_basis_points(self):
        source = series([("2022", 3.0), ("2023", 3.3)], frequency="A", unit="Per Cent", change_kind="percentage_point")
        comparison = change(evaluate_series(source, "2023-12-31"))
        self.assertEqual(comparison["value"], 0.3)
        self.assertEqual(comparison["unit"], "percentage points")
        source["change_kind"] = "basis_point"
        comparison = change(evaluate_series(source, "2023-12-31"))
        self.assertEqual(comparison["value"], 30)
        self.assertEqual(comparison["unit"], "basis points")

    def test_negative_denominator_is_disclosed(self):
        evaluation = evaluate_series(series([("2022", -10), ("2023", -5)], frequency="A"), "2023-12-31")
        self.assertEqual(change(evaluation)["value"], -50)
        self.assertTrue(any("negative signed denominator" in warning for warning in evaluation["quality"]["warnings"]))

    def test_overflow_is_an_unavailable_change_not_an_infinite_number(self):
        evaluation = evaluate_series(series([("2022", 1e-308), ("2023", 1e308)], frequency="A"), "2023-12-31")
        comparison = change(evaluation)
        self.assertIsNone(comparison["value"])
        self.assertIn("finite numeric range", comparison["reason"])

    def test_sorting_preserves_original_evidence_without_mutating_input(self):
        source = series([("2024-Q1", 110), ("2023-Q1", 100)])
        source["provenance"] = {"raw_file": "snapshots/original.json"}
        before = deepcopy(source)
        evaluation = evaluate_series(source, "2024-03-31")
        self.assertEqual([row["period"] for row in evaluation["observations"]], ["2023-Q1", "2024-Q1"])
        self.assertEqual(change(evaluation)["evidence"], source["observations"])
        self.assertEqual(source, before)
        evaluation["metadata"]["provenance"]["raw_file"] = "changed"
        evaluation["latest"]["value"] = -1
        self.assertEqual(source, before)


class CutoffAndQualityTests(unittest.TestCase):
    def test_period_end_cutoff_excludes_an_incomplete_quarter(self):
        source = series([("2023-Q4", 100), ("2024-Q1", 110)])
        before = evaluate_series(source, "2024-03-30")
        on_end = evaluate_series(source, "2024-03-31")
        self.assertEqual(before["latest"]["period"], "2023-Q4")
        self.assertEqual(len(before["observations"]), 1)
        self.assertEqual(on_end["latest"]["period"], "2024-Q1")

    def test_month_end_handles_leap_year(self):
        source = series([("2024-01", 100), ("2024-02", 110)], frequency="M")
        self.assertEqual(evaluate_series(source, "2024-02-28")["latest"]["period"], "2024-01")
        self.assertEqual(evaluate_series(source, "2024-02-29")["latest"]["period"], "2024-02")

    def test_source_backed_midyear_population_is_not_excluded_until_december(self):
        source = series([("2024", 100), ("2025", 101), ("2026", 102)], frequency="A", unit="Persons")
        for row in source["observations"]:
            row["observation_date"] = row["period"] + "-06-30"
        source["observations"][-1]["published_at"] = "2026-09-25"
        evaluation = evaluate_series(source, "2026-10-01")
        self.assertEqual(evaluation["latest"]["period"], "2026")
        self.assertEqual(evaluation["latest"]["observation_date"], "2026-06-30")
        self.assertEqual(evaluation["quality"]["lag_periods"], 0)
        self.assertTrue(evaluation["quality"]["eligible"])
        self.assertEqual(change(evaluation)["base_period"], "2025")

    def test_known_future_publication_is_excluded(self):
        source = series([("2023-Q4", 100), ("2024-Q1", 110)])
        source["observations"][-1]["published_at"] = "2024-04-15"
        evaluation = evaluate_series(source, "2024-04-01")
        self.assertEqual(evaluation["latest"]["period"], "2023-Q4")
        self.assertTrue(any("known publication date after" in warning for warning in evaluation["quality"]["warnings"]))
        self.assertEqual(evaluate_series(source, "2024-04-15")["latest"]["period"], "2024-Q1")

    def test_unknown_publication_date_never_inferred_from_table_update(self):
        source = series([("2023-Q4", 100)], source_updated_at="2026-10-01")
        evaluation = evaluate_series(source, "2024-01-01")
        self.assertEqual(evaluation["latest"]["period"], "2023-Q4")
        self.assertNotIn("published_at", evaluation["latest"])
        self.assertTrue(any("Latest-vintage" in warning for warning in evaluation["quality"]["warnings"]))

    def test_missing_fraction_counts_implicit_gaps_and_explicit_nulls(self):
        source = series([("2023-Q1", 100), ("2023-Q2", None), ("2023-Q4", 120), ("2024-Q1", 130)])
        quality = evaluate_series(source, "2024-03-31")["quality"]
        self.assertEqual(quality["valid_count"], 3)
        self.assertEqual(quality["expected_count"], 5)
        self.assertEqual(quality["missing_count"], 2)
        self.assertEqual(quality["missing_fraction"], 0.4)
        self.assertTrue(any("Incomplete history" in reason for reason in quality["reasons"]))

    def test_latest_null_uses_previous_finite_period_and_discloses_it(self):
        source = series([("2023-Q4", 100), ("2024-Q1", None)])
        evaluation = evaluate_series(source, "2024-03-31")
        self.assertEqual(evaluation["latest"]["period"], "2023-Q4")
        self.assertEqual(evaluation["quality"]["lag_periods"], 1)
        self.assertTrue(any("most recent retained period has no value" in warning for warning in evaluation["quality"]["warnings"]))

    def test_empty_and_all_null_data_are_ineligible_with_no_nan(self):
        for source in [series(), series([("2023-Q1", None)])]:
            with self.subTest(source=source):
                evaluation = evaluate_series(source, "2024-03-31")
                self.assertIsNone(evaluation["latest"])
                self.assertFalse(evaluation["quality"]["eligible"])
                self.assertEqual(evaluation["quality"]["score"], 0)
                self.assertEqual(evaluation["quality"]["missing_fraction"], 1)
                self.assertTrue(all(item["value"] is None for item in evaluation["changes"]))

    def test_frequency_specific_history_minimum_is_transparent(self):
        examples = {
            "A": [(str(year), year) for year in range(2022, 2025)],
            "Q": [(f"{year}-Q{quarter}", year) for year in (2023, 2024) for quarter in range(1, 5)],
            "M": [(f"{year}-{month:02d}", year) for year in (2023, 2024) for month in range(1, 13)],
        }
        for frequency, values in examples.items():
            with self.subTest(frequency=frequency):
                evaluation = evaluate_series(series(values, frequency=frequency), "2024-12-31")
                self.assertTrue(evaluation["quality"]["eligible"])
                self.assertEqual(evaluation["quality"]["thresholds"]["minimum_valid"], len(values))
                shortened = evaluate_series(series(values[1:], frequency=frequency), "2024-12-31")
                self.assertFalse(shortened["quality"]["eligible"])
                self.assertTrue(any("Insufficient history" in reason for reason in shortened["quality"]["reasons"]))

    def test_staleness_boundary_does_not_fill_quota_with_old_series(self):
        source = series([("2020", 100), ("2021", 101), ("2022", 102)], frequency="A")
        at_limit = evaluate_series(source, "2024-12-31")
        past_limit = evaluate_series(source, "2025-12-31")
        self.assertTrue(at_limit["quality"]["eligible"])
        self.assertFalse(past_limit["quality"]["eligible"])
        self.assertEqual(past_limit["quality"]["lag_periods"], 3)
        self.assertIn("Stale data", " ".join(past_limit["quality"]["reasons"]))

    def test_completeness_threshold_is_inclusive_and_uses_calendar_span(self):
        values = [(str(year), year) for year in range(2021, 2025)]
        values[1] = ("2022", None)
        quality = evaluate_series(series(values, frequency="A"), "2024-12-31")["quality"]
        self.assertTrue(quality["eligible"])
        self.assertEqual(quality["missing_fraction"], 0.25)
        self.assertIn("Not predictive validation", quality["score_definition"])

    def test_sparse_early_archives_do_not_disqualify_complete_recent_history(self):
        values = [("1980", 80), ("1990", 90)] + [(str(year), year) for year in range(2017, 2027)]
        source = series(values, frequency="A")
        evaluation = evaluate_series(source, "2026-12-31")
        quality = evaluation["quality"]
        self.assertTrue(quality["eligible"])
        self.assertEqual(quality["missing_fraction"], 0)
        self.assertEqual(quality["window_start_period"], "2017")
        self.assertEqual(quality["window_end_period"], "2026")
        self.assertEqual(quality["window_valid_count"], 10)
        self.assertEqual(quality["valid_count"], 10)
        self.assertEqual(quality["total_valid_count"], 12)
        self.assertEqual(len(evaluation["observations"]), 12)

    def test_long_archives_cannot_substitute_for_insufficient_recent_history(self):
        values = [(str(year), year) for year in range(1980, 1990)] + [("2026", 2026)]
        quality = evaluate_series(series(values, frequency="A"), "2026-12-31")["quality"]
        self.assertFalse(quality["eligible"])
        self.assertEqual(quality["window_valid_count"], 1)
        self.assertEqual(quality["total_valid_count"], 11)
        self.assertIn("Insufficient history", " ".join(quality["reasons"]))

    def test_annual_midyear_reference_anchors_recent_window_in_current_year(self):
        source = series([(str(year), year) for year in range(2016, 2027)], frequency="A")
        for row in source["observations"]:
            row["observation_date"] = row["period"] + "-06-30"
        quality = evaluate_series(source, "2026-10-01")["quality"]
        self.assertEqual(quality["window_start_period"], "2017")
        self.assertEqual(quality["window_end_period"], "2026")
        self.assertEqual(quality["window_valid_count"], 10)


class ValidationTests(unittest.TestCase):
    def test_invalid_as_of(self):
        for value in ["2024-02-30", "2024-2-01", "2024-01-01T00:00:00", None, 2024]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate_series(series(), value)

    def test_invalid_frequencies_and_periods(self):
        for frequency, period in [("D", "2024-01-01"), ("Q", "2024-Q5"), ("Q", "2024-01"), ("M", "2024-13"), ("M", "2024-1"), ("A", "0000"), ("A", "2024-Q1")]:
            with self.subTest(frequency=frequency, period=period), self.assertRaises(ValueError):
                evaluate_series(series([(period, 1)], frequency=frequency), "2024-12-31")

    def test_invalid_numeric_values_including_bools_and_nonfinite(self):
        for value in [True, "1", float("nan"), float("inf"), -float("inf"), {}, 10 ** 1000]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                evaluate_series(series([("2024-Q1", value)]), "2024-03-31")

    def test_duplicate_periods_rejected_even_when_after_cutoff(self):
        with self.assertRaisesRegex(ValueError, "Duplicate period"):
            evaluate_series(series([("2025-Q1", 10), ("2025-Q1", 11)]), "2024-01-01")

    def test_schema_and_unit_errors(self):
        for patch in [{"id": ""}, {"unit": ""}, {"frequency": []}, {"change_kind": "ratio"}, {"observations": {}}, {"observations": [{"period": "2024-Q1"}]}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                evaluate_series(series(**patch), "2024-03-31")
        for kind in ("basis_point", "percentage_point"):
            for unit in ("Fraction", "Basis Points", "Persons", "Percentage Points"):
                with self.subTest(kind=kind, unit=unit), self.assertRaisesRegex(ValueError, "percentage units"):
                    evaluate_series(series(unit=unit, change_kind=kind), "2024-03-31")

    def test_comparisons_override_rejects_unknown_empty_duplicate_or_annual_previous(self):
        for comparisons in [[], "year_on_year", ["year_on_year", "year_on_year"], ["quarterly"], [{}]]:
            with self.subTest(comparisons=comparisons), self.assertRaises(ValueError):
                evaluate_series(series(comparisons=comparisons), "2024-03-31")
        with self.assertRaises(ValueError):
            evaluate_series(series(frequency="A", comparisons=["previous_period"]), "2024-12-31")

    def test_invalid_reference_dates_and_publication_dates(self):
        examples = [
            ("A", "2026", "observation_date", "2025-06-30"),
            ("Q", "2026-Q2", "observation_date", "2026-07-01"),
            ("M", "2026-06", "observation_date", "2026-05-31"),
            ("A", "2026", "published_at", "2026-02-30"),
        ]
        for frequency, period, key, value in examples:
            source = series([(period, 100)], frequency=frequency)
            source["observations"][0][key] = value
            with self.subTest(example=(frequency, period, key, value)), self.assertRaises(ValueError):
                evaluate_series(source, "2026-10-01")


class SelectionTests(unittest.TestCase):
    def test_theme_coverage_precedes_second_indicator_in_same_theme(self):
        evaluations = [candidate("a", 100, "demand"), candidate("b", 99, "demand"), candidate("c", 70, "supply"), candidate("d", 60, "financing")]
        selected = select_candidates(evaluations, 3)
        self.assertEqual(selected["selected_ids"], ["a", "c", "d"])
        self.assertEqual(select_candidates(evaluations, 4)["selected_ids"], ["a", "c", "d", "b"])
        self.assertFalse(next(item for item in selected["decisions"] if item["id"] == "b")["selected"])

    def test_ineligible_high_score_cannot_fill_requested_capacity(self):
        result = select_candidates([candidate("bad", 100, "demand", False), candidate("good", 70, "supply")], 5)
        self.assertEqual(result["selected_ids"], ["good"])
        excluded = next(item for item in result["decisions"] if item["id"] == "bad")
        self.assertIn("Insufficient history", excluded["reason"])

    def test_ties_and_decisions_are_deterministic_after_input_reordering(self):
        evaluations = [candidate("z", 80, "supply"), candidate("a", 80, "demand"), candidate("b", 80, "demand")]
        self.assertEqual(select_candidates(evaluations, 2), select_candidates(list(reversed(evaluations)), 2))
        self.assertEqual(select_candidates(evaluations, 2)["selected_ids"], ["a", "z"])

    def test_theme_normalization_and_unspecified_themes(self):
        evaluations = [candidate("a", 90, "Demand"), candidate("b", 85, " demand "), candidate("c", 80, None), candidate("d", 79, ""), candidate("e", 60, "supply")]
        self.assertEqual(select_candidates(evaluations, 3)["selected_ids"], ["a", "c", "e"])

    def test_selection_family_prevents_supply_subthemes_crowding_out_other_channels(self):
        supply_a = candidate("supply_a", 100, "vacancy")
        supply_b = candidate("supply_b", 99, "completions")
        supply_c = candidate("supply_c", 98, "pipeline")
        for item in (supply_a, supply_b, supply_c):
            item["metadata"]["selection_family"] = "housing_supply"
        demand = candidate("demand", 80, "population")
        financing = candidate("financing", 70, "interest_rates")
        evaluations = [supply_a, supply_b, supply_c, demand, financing]
        selected = select_candidates(evaluations, 3)
        self.assertEqual(selected["selected_ids"], ["supply_a", "demand", "financing"])
        self.assertEqual(select_candidates(evaluations, 4)["selected_ids"], ["supply_a", "demand", "financing", "supply_b"])
        self.assertIn("housing_supply", next(item for item in selected["decisions"] if item["id"] == "supply_a")["reason"])

    def test_empty_selection_family_falls_back_to_theme(self):
        a, b = candidate("a", 90, "demand"), candidate("b", 80, "demand")
        a["metadata"]["selection_family"] = ""
        self.assertEqual(select_candidates([a, b, candidate("c", 70, "supply")], 2)["selected_ids"], ["a", "c"])

    def test_empty_selection_and_zero_limit_still_explain_all_candidates(self):
        self.assertEqual(select_candidates([], 5)["decisions"], [])
        result = select_candidates([candidate("a", 80, "demand")], 0)
        self.assertEqual(result["selected_ids"], [])
        self.assertEqual(len(result["decisions"]), 1)
        self.assertFalse(result["decisions"][0]["selected"])

    def test_reject_invalid_selection_input(self):
        for limit in [-1, 1.5, True, "5"]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                select_candidates([], limit)
        a = candidate("a", 80, "demand")
        with self.assertRaisesRegex(ValueError, "Duplicate candidate"):
            select_candidates([a, a])
        for patch in [{"score": float("nan")}, {"score": 101}, {"score": 10 ** 1000}, {"score": True}, {"eligible": "yes"}, {"reasons": "error"}]:
            invalid = deepcopy(a)
            invalid["quality"].update(patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                select_candidates([invalid])


if __name__ == "__main__":
    unittest.main()
