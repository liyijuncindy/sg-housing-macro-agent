"""Offline contract and adversarial-output checks; these never call OpenAI."""

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from housing_agent.agent import AgentError, run_agent


def candidate(series_id="income", eligible=True):
    return {"id": series_id,
        "metadata": {"name": "Income", "theme": "demand", "definition": "Household income",
                     "source_agency": "Official agency", "source_url": "https://example.test/data",
                     "mechanism": {"sales": "Income may support affordability.",
                                   "rents": "Income may support rental demand."}},
        "quality": {"eligible": eligible, "score": 90, "reasons": [], "warnings": []},
        "latest": {"period": "2026-Q2", "value": 108},
        "changes": [{"id": series_id + ":year_on_year", "value": 8, "unit": "%",
                     "evidence": [{"period": "2025-Q2", "value": 100},
                                  {"period": "2026-Q2", "value": 108}]}]}


def submission():
    return {"selected_ids": ["income"],
        "decisions": [{"id": "income", "selected": True,
                       "reason": "Eligible income data may inform housing affordability."}],
        "narratives": [{"id": "income", "sales": "Income may support purchase affordability.",
                        "rents": "Income may influence tenant spending capacity.",
                        "lag": "Housing responses may follow changes in household resources with a delay.",
                        "limitations": "Association does not establish causality or predictive accuracy.",
                        "evidence_ids": ["income:latest", "income:year_on_year"]}]}


def response(name, arguments, turn=1):
    return {"id": f"response_{turn}", "status": "completed",
        "output": [{"type": "function_call", "name": name, "call_id": f"call_{turn}",
                    "arguments": json.dumps(arguments)}],
        "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30}}


def sequence(final=None):
    return [response("list_candidates", {"query": ""}),
            response("inspect_candidate", {"ids": ["income"]}, 2),
            response("submit_analysis", final if final is not None else submission(), 3)]


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.trace = Path(self.temp.name) / "trace.json"
        self.client = Mock()
        self.constructor = Mock(return_value=self.client)
        self.environment = patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-secret"}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.sdk = patch.dict(sys.modules, {"openai": SimpleNamespace(OpenAI=self.constructor)})
        self.sdk.start()
        self.addCleanup(self.sdk.stop)

    def run_mock(self, responses, evaluations=None, limit=2):
        self.client.responses.create.side_effect = responses
        return run_agent(evaluations if evaluations is not None else [candidate(), candidate("vacancy", False)],
                         "2026-10-01", limit, "externally-chosen-model", self.trace,
                         max_turns=len(responses), max_output_tokens=1200)

    def read_trace(self):
        return json.loads(self.trace.read_text())

    def test_real_tool_loop_is_evidence_constrained_and_audited(self):
        result = self.run_mock(sequence())
        self.assertEqual(result["selected_ids"], ["income"])
        self.assertEqual(result["usage"], {"input_tokens": 60, "output_tokens": 30,
                                          "total_tokens": 90, "requests": 3})
        self.assertEqual(len(result["decisions"]), 2)
        self.assertEqual(result["decisions"][1]["reason_origin"], "system")
        self.assertIn("System exclusion", result["decisions"][1]["reason"])
        self.assertEqual(result["method"], "openai_responses_constrained_agent")
        trace = self.read_trace()
        self.assertEqual(trace["status"], "completed")
        facts = trace["events"][1]["tool_results"][0]["output"]["candidates"][0]
        self.assertEqual(facts["evidence"]["income:latest"]["value"], 108)
        self.assertTrue(trace["events"][-1]["validation"]["accepted"])
        for call in self.client.responses.create.call_args_list:
            self.assertEqual(call.kwargs["model"], "externally-chosen-model")
            self.assertEqual(call.kwargs["max_output_tokens"], 1200)
            self.assertFalse(call.kwargs["store"])
            self.assertFalse(call.kwargs["parallel_tool_calls"])
        self.assertEqual(self.constructor.call_args.kwargs["timeout"], 60.0)
        self.assertEqual(self.constructor.call_args.kwargs["max_retries"], 0)
        self.assertNotIn("sk-test-secret", self.trace.read_text())
        self.client.close.assert_called_once()

    def test_no_key_fails_without_import_or_request_and_records_failure(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(AgentError, "OPENAI_API_KEY is missing"):
                self.run_mock(sequence())
        self.constructor.assert_not_called()
        self.assertEqual(self.read_trace()["status"], "failed")

    def test_selected_candidate_must_have_been_inspected(self):
        with self.assertRaisesRegex(AgentError, "turn budget"):
            self.run_mock([response("list_candidates", {"query": ""}),
                           response("submit_analysis", submission(), 2)])
        self.assertIn("inspect_candidate", self.read_trace()["events"][-1]["validation"]["error"])

    def test_inspect_requires_actual_discovery(self):
        with self.assertRaisesRegex(AgentError, "turn budget"):
            self.run_mock([response("inspect_candidate", {"ids": ["income"]})])
        self.assertIn("list_candidates", self.read_trace()["events"][0]["validation"]["error"])

    def test_numeric_and_certainty_and_link_prose_is_rejected(self):
        for text in ("Prices may grow 10%.", "Prices may rise ten percent.",
                     "Rent will increase.", "This causes rising prices.",
                     "This must cause rising rents.", "The model predicts higher prices.",
                     "Prices are guaranteed to rise.", "Income reached half the former level.",
                     "Rents doubled the rate of growth.", "The rate changed by one percentage point.",
                     "See https://fabricated.test for evidence.", "See [income:latest]."):
            with self.subTest(text=text):
                invalid = submission()
                invalid["narratives"][0]["sales"] = text
                with self.assertRaisesRegex(AgentError, "turn budget"):
                    self.run_mock(sequence(invalid))
                self.assertFalse(self.read_trace()["events"][-1]["validation"]["accepted"])

    def test_ordinary_qualitative_language_does_not_trigger_false_rejections(self):
        for text in ("The response may occur in a later quarter.",
                     "Common causes may influence both employment and housing demand.",
                     "This does not predict higher prices.",
                     "Correlation does not prove causality.",
                     "This is not a forecast of housing prices.",
                     "Borrowing costs may cause lower housing demand.",
                     "Income is one of the relevant affordability indicators.",
                     "Year on year percentage changes may reflect base effects.",
                     "Avoid double counting related housing supply indicators."):
            with self.subTest(text=text):
                valid = submission()
                valid["narratives"][0]["limitations"] = text
                result = self.run_mock(sequence(valid))
                self.assertEqual(result["narratives"]["income"]["limitations"], text)

    def test_source_reference_dates_and_selection_families_reach_the_model(self):
        item = candidate()
        item["metadata"]["selection_family"] = "housing_supply"
        item["latest"]["observation_date"] = "2026-06-30"
        self.run_mock(sequence(), [item])
        trace = self.read_trace()
        card = trace["events"][0]["tool_results"][0]["output"]["candidates"][0]
        inspected = trace["events"][1]["tool_results"][0]["output"]["candidates"][0]
        self.assertEqual(card["selection_family"], "housing_supply")
        self.assertEqual(inspected["metadata"]["selection_family"], "housing_supply")
        self.assertEqual(inspected["latest"]["observation_date"], "2026-06-30")
        self.assertIn("otherwise the observation period end", trace["instructions"])
        self.assertIn("not a mandatory family quota", trace["instructions"])

    def test_fabricated_and_other_series_evidence_is_rejected(self):
        for evidence in ([], ["invented:latest"], ["vacancy:latest"], ["income:unprovided"],
                         ["income:latest", "income:latest"]):
            with self.subTest(evidence=evidence):
                invalid = submission()
                invalid["narratives"][0]["evidence_ids"] = evidence
                with self.assertRaisesRegex(AgentError, "turn budget"):
                    self.run_mock(sequence(invalid))
                self.assertFalse(self.read_trace()["events"][-1]["validation"]["accepted"])

    def test_unknown_duplicate_and_ineligible_selection_is_rejected(self):
        for selected in (["unknown"], ["income", "income"], ["vacancy"], []):
            with self.subTest(selected=selected):
                invalid = submission()
                invalid["selected_ids"] = selected
                with self.assertRaisesRegex(AgentError, "turn budget"):
                    self.run_mock(sequence(invalid))

    def test_selection_limit_enforced(self):
        invalid = submission()
        invalid["selected_ids"].append("vacancy")
        with self.assertRaisesRegex(AgentError, "turn budget"):
            self.run_mock(sequence(invalid), [candidate(), candidate("vacancy")], limit=1)
        self.assertIn("limit", self.read_trace()["events"][-1]["validation"]["error"])

    def test_duplicate_narrative_and_missing_selected_reason_are_rejected(self):
        duplicate = submission()
        duplicate["narratives"].append(deepcopy(duplicate["narratives"][0]))
        no_reason = submission()
        no_reason["decisions"] = []
        for invalid in (duplicate, no_reason):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(AgentError, "turn budget"):
                    self.run_mock(sequence(invalid))

    def test_validation_failure_can_be_repaired_within_budget(self):
        invalid = submission()
        invalid["narratives"][0]["sales"] = "Sales may increase 12%."
        responses = sequence(invalid) + [response("submit_analysis", submission(), 4)]
        result = self.run_mock(responses)
        self.assertEqual(result["selected_ids"], ["income"])
        events = self.read_trace()["events"]
        self.assertFalse(events[2]["validation"]["accepted"])
        self.assertTrue(events[3]["validation"]["accepted"])
        self.assertEqual(result["usage"]["requests"], 4)

    def test_reasoning_and_function_outputs_are_carried_to_next_request(self):
        responses = sequence()
        reasoning = {"type": "reasoning", "id": "reasoning_item", "summary": []}
        responses[0]["output"].insert(0, reasoning)
        captured = []

        def create(**kwargs):
            captured.append(deepcopy(kwargs))
            return responses[len(captured) - 1]

        self.client.responses.create.side_effect = create
        run_agent([candidate()], "2026-10-01", 1, "test-model", self.trace, max_turns=3)
        self.assertIn(reasoning, captured[1]["input"])
        tool_output = [item for item in captured[1]["input"] if item.get("type") == "function_call_output"]
        self.assertEqual(tool_output[0]["call_id"], "call_1")
        self.assertIn("candidates", json.loads(tool_output[0]["output"]))

    def test_api_failure_is_explicit_and_secret_is_redacted(self):
        with self.assertRaises(AgentError) as error:
            self.run_mock([RuntimeError("Request failed for sk-test-secret")])
        self.assertNotIn("sk-test-secret", str(error.exception))
        self.assertNotIn("sk-test-secret", self.trace.read_text())
        self.assertEqual(self.read_trace()["status"], "failed")

    def test_incomplete_or_text_only_response_fails_closed(self):
        incomplete = response("submit_analysis", submission())
        incomplete["status"] = "incomplete"
        for item in (incomplete, {"status": "completed", "output": [{"type": "message", "content": "hello"}]}):
            with self.subTest(item=item):
                with self.assertRaises(AgentError):
                    self.run_mock([item])
                self.assertEqual(self.read_trace()["status"], "failed")

    def test_search_filters_without_inventing_candidates(self):
        responses = [response("list_candidates", {"query": "no match"}),
                     response("inspect_candidate", {"ids": ["income"]}, 2)]
        with self.assertRaises(AgentError):
            self.run_mock(responses)
        trace = self.read_trace()
        self.assertEqual(trace["events"][0]["tool_results"][0]["output"]["candidates"], [])
        self.assertFalse(trace["events"][1]["validation"]["accepted"])

    def test_strict_schemas_are_complete(self):
        self.run_mock(sequence())

        def check(schema):
            if schema.get("type") == "object":
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), set(schema["properties"]))
                for child in schema["properties"].values():
                    check(child)
            elif schema.get("type") == "array":
                check(schema["items"])

        for tool in self.client.responses.create.call_args.kwargs["tools"]:
            self.assertTrue(tool["strict"])
            check(tool["parameters"])


if __name__ == "__main__":
    unittest.main()
