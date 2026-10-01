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

from housing_agent.agent import AgentError, _facts, _quality_notes, run_agent


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


def chat_response(name, arguments, turn=1):
    return {"id": f"chatcmpl-{turn}", "object": "chat.completion", "created": 1790812800,
            "model": "qwen3.6:35b-served", "choices": [{"index": 0, "finish_reason": "tool_calls",
                "message": {"role": "assistant", "content": None, "tool_calls": [{
                    "id": f"chat_call_{turn}", "type": "function", "function": {
                        "name": name, "arguments": json.dumps(arguments)}}]}}],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}}


def chat_sequence(final=None):
    return [chat_response("list_candidates", {"query": ""}),
            chat_response("inspect_candidate", {"ids": ["income"]}, 2),
            chat_response("submit_analysis", final if final is not None else submission(), 3)]


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

    def run_soclaas(self, responses, captured=None):
        remaining = iter(responses)

        def create(**kwargs):
            if captured is not None:
                captured.append(deepcopy(kwargs))
            value = next(remaining)
            if isinstance(value, Exception):
                raise value
            return value

        self.client.chat.completions.create.side_effect = create
        with patch.dict(os.environ, {"SOCLAAS_API_KEY": "clsk_test-secret"}):
            return run_agent([candidate(), candidate("vacancy", False)], "2026-10-01", 2,
                             "qwen3.6:35b", self.trace, max_turns=len(responses),
                             max_output_tokens=1200, provider="soclaas")

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
        self.assertEqual(inspected["evidence"]["income:latest"]["observation_date"], "2026-06-30")
        self.assertIn("otherwise the observation period end", trace["instructions"])
        self.assertIn("not a mandatory family quota", trace["instructions"])

    def test_inspection_projection_preserves_analysis_facts_without_raw_payload_duplication(self):
        item = candidate()
        item["metadata"].update({"unit": "Million Dollars", "frequency": "Q",
            "scope": "Aggregate national income, not per household", "selection_family": "household_income",
            "seasonal_adjustment": "Not seasonally adjusted", "availability_note": "Latest downloaded vintage",
            "row_footnote": "Definition changed in the historic series", "source_footnote": "irrelevant " * 2000,
            "provenance": {"raw_file": "raw/data.json", "raw_sha256": "private-to-audit-hash"}})
        item["changes"].append({"id": "income:previous_period", "comparison": "previous_period",
                                "value": None, "reason": "Calendar baseline observation is missing"})
        original = deepcopy(item)
        projected = _facts(item)
        for field in ("definition", "unit", "frequency", "scope", "selection_family", "mechanism",
                      "seasonal_adjustment", "availability_note", "row_footnote", "source_url"):
            self.assertEqual(projected["metadata"][field], item["metadata"][field])
        self.assertNotIn("source_footnote", projected["metadata"])
        self.assertNotIn("provenance", projected["metadata"])
        self.assertNotIn("latest", projected)
        self.assertNotIn("changes", projected)
        self.assertEqual(projected["evidence"]["income:latest"], item["latest"])
        self.assertEqual(projected["evidence"]["income:year_on_year"], item["changes"][0])
        self.assertEqual(projected["evidence_ids"], ["income:latest", "income:year_on_year"])
        self.assertEqual(projected["unavailable_comparisons"][0]["reason"],
                         "Calendar baseline observation is missing")
        self.assertLess(len(json.dumps(projected)), len(json.dumps(item)) // 3)
        self.assertEqual(item, original)

    def test_shared_quality_policy_is_returned_once_and_scoring_metrics_are_preserved(self):
        items = [candidate(), candidate("vacancy", False)]
        for item in items:
            item["quality"].update({"warnings": ["Shared vintage caveat"],
                "score_definition": "Shared usability scoring policy", "score_components": {"history": 30},
                "thresholds": {"minimum_valid": 3}, "valid_count": 20, "missing_fraction": 0.0,
                "lag_periods": 2})
        items[0]["quality"]["warnings"].append("Specific quality issue")
        self.run_mock(sequence(), items)
        result = self.read_trace()["events"][0]["tool_results"][0]["output"]
        self.assertEqual(set(result["quality_notes"].values()),
                         {"Shared vintage caveat", "Shared usability scoring policy"})
        serialized = json.dumps(result)
        self.assertEqual(serialized.count("Shared vintage caveat"), 1)
        self.assertEqual(serialized.count("Shared usability scoring policy"), 1)
        quality = result["candidates"][0]["quality"]
        self.assertEqual(quality["score_components"], {"history": 30})
        self.assertEqual(quality["lag_periods"], 2)
        self.assertEqual(quality["warnings"], ["Specific quality issue"])
        self.assertTrue(quality["warning_refs"])
        self.assertTrue(quality["score_definition_ref"])

    def test_metadata_text_bounds_are_explicit_and_do_not_modify_evidence(self):
        item = candidate()
        item["metadata"]["definition"] = "Long source definition " * 200
        item["metadata"]["mechanism"]["sales"] = "Long explanation " * 200
        projected = _facts(item)
        self.assertIn("definition", projected["metadata"]["excerpted_fields"])
        self.assertIn("mechanism.sales", projected["metadata"]["excerpted_fields"])
        self.assertLess(len(projected["metadata"]["definition"]), 1300)
        self.assertLess(len(projected["metadata"]["mechanism"]["sales"]), 900)
        self.assertEqual(projected["evidence"]["income:year_on_year"], item["changes"][0])

    def test_numeric_tenor_feedback_identifies_token_and_provides_concrete_repair(self):
        invalid = submission()
        invalid["narratives"][0]["sales"] = "The three-month SORA benchmark may influence affordability."
        self.run_mock(sequence(invalid) + [response("submit_analysis", submission(), 4)])
        error = self.read_trace()["events"][2]["validation"]["error"]
        self.assertIn("offending token 'three'", error)
        self.assertIn("'the SORA benchmark'", error)
        self.assertIn("numeric tenor labels", self.read_trace()["instructions"])

    def test_population_year_failure_forces_submit_with_explicit_trusted_wording_repair(self):
        examples = [
            ("Population is not household formation; pre-1990 concepts and the 2003 coverage change "
             "may limit comparability.", ["pre-1990", "2003"]),
            ("The twenty03 coverage change may limit comparability.", ["twenty03"]),
            ("The two thousand three coverage change may limit comparability.", ["two thousand three"]),
        ]
        for wording, fragments in examples:
            with self.subTest(wording=wording):
                invalid = submission()
                invalid["narratives"][0]["limitations"] = wording
                repaired = submission()
                repaired["narratives"][0]["limitations"] = (
                    "Historical definition and coverage changes may limit comparability.")
                captured = []
                self.run_soclaas(chat_sequence(invalid) + [chat_response("submit_analysis", repaired, 4)], captured)
                event = self.read_trace()["events"][2]
                error = event["validation"]["error"]
                for fragment in fragments:
                    self.assertIn(fragment, error)
                self.assertIn("do not translate digits into words", error)
                self.assertNotIn("SORA", error)
                self.assertEqual(captured[3]["tool_choice"],
                                 {"type": "function", "function": {"name": "submit_analysis"}})
                self.assertEqual(captured[3]["messages"][-2]["role"], "tool")
                self.assertEqual(captured[3]["messages"][-1]["role"], "user")
                self.assertEqual(captured[3]["messages"][-1]["content"], event["repair_instruction"])
                self.assertIn("income.limitations", event["repair_instruction"])
                self.assertEqual(self.read_trace()["usage"]["requests"], 4)

    def test_numeric_error_does_not_force_wording_repair_when_evidence_needs_lookup(self):
        invalid = submission()
        # Decision prose is checked before narrative evidence; the repair gate
        # must still notice that the evidence is invalid instead of forcing submit.
        invalid["decisions"][0]["reason"] = "The 2003 definition may limit comparability."
        invalid["narratives"][0]["evidence_ids"] = ["income:invented"]
        captured = []
        self.run_soclaas(chat_sequence(invalid) + [
            chat_response("inspect_candidate", {"ids": ["income"]}, 4),
            chat_response("submit_analysis", submission(), 5)], captured)
        self.assertEqual(captured[3]["tool_choice"], "required")
        self.assertEqual(captured[3]["messages"][-1]["role"], "tool")
        self.assertNotIn("repair_instruction", self.read_trace()["events"][2])

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
        self.assertEqual(self.client.responses.create.call_args.kwargs["tool_choice"],
                         {"type": "function", "name": "submit_analysis"})

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

    def test_soclaas_chat_loop_forces_safe_phases_and_uses_chat_wire_format(self):
        captured = []
        with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://wrong.example.test",
                                     "OPENAI_ORGANIZATION": "unrelated-account",
                                     "OPENAI_PROJECT_ID": "unrelated-project"}):
            result = self.run_soclaas(chat_sequence(), captured)
        self.client.responses.create.assert_not_called()
        options = self.constructor.call_args.kwargs
        self.assertEqual(options["api_key"], "clsk_test-secret")
        self.assertEqual(options["base_url"], "https://soclaas-api.comp.nus.edu.sg/v1")
        self.assertEqual(options["organization"], "")
        self.assertEqual(options["project"], "")
        self.assertEqual(options["timeout"], 60.0)
        self.assertEqual(options["max_retries"], 0)
        self.assertEqual(captured[0]["tool_choice"],
                         {"type": "function", "function": {"name": "list_candidates"}})
        self.assertEqual(captured[1]["tool_choice"],
                         {"type": "function", "function": {"name": "inspect_candidate"}})
        self.assertEqual(captured[2]["tool_choice"], "required")
        self.assertEqual([message["role"] for message in captured[1]["messages"]],
                         ["system", "user", "assistant", "tool"])
        self.assertEqual(captured[1]["messages"][-1]["tool_call_id"], "chat_call_1")
        self.assertIn("candidates", json.loads(captured[1]["messages"][-1]["content"]))
        for call in captured:
            self.assertEqual(call["reasoning_effort"], "none")
            self.assertEqual(call["max_tokens"], 1200)
            self.assertEqual(call["model"], "qwen3.6:35b")
            self.assertFalse(call["parallel_tool_calls"])
            self.assertNotIn("max_output_tokens", call)
            for tool in call["tools"]:
                self.assertEqual(set(tool), {"type", "function"})
                self.assertEqual(tool["type"], "function")
                self.assertTrue(tool["function"]["strict"])
        self.assertEqual(result["method"], "soclaas_chat_completions_constrained_agent")
        self.assertEqual(result["usage"], {"input_tokens": 33, "output_tokens": 21,
                                          "total_tokens": 54, "requests": 3})
        trace = self.read_trace()
        self.assertEqual(trace["provider"], "soclaas")
        self.assertEqual(trace["api_mode"], "chat_completions")
        self.assertEqual(trace["model"], "qwen3.6:35b")
        self.assertEqual(trace["actual_model"], "qwen3.6:35b-served")
        self.assertEqual(trace["actual_models"], ["qwen3.6:35b-served"])
        self.assertIn("ended_at", trace)
        self.assertGreaterEqual(trace["elapsed_seconds"], 0)
        self.assertNotIn("clsk_test-secret", self.trace.read_text())

    def test_provider_credentials_never_fall_back_to_each_other(self):
        for provider, environment, missing in (
            ("soclaas", {"OPENAI_API_KEY": "sk-openai-only"}, "SOCLAAS_API_KEY"),
            ("openai", {"SOCLAAS_API_KEY": "clsk_soclaas-only"}, "OPENAI_API_KEY"),
        ):
            with self.subTest(provider=provider), patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(AgentError, missing + " is missing"):
                    run_agent([candidate()], "2026-10-01", 1, "chosen-model", self.trace, provider=provider)
                self.assertEqual(self.read_trace()["status"], "failed")
        self.constructor.assert_not_called()

    def test_soclaas_rejects_inherited_custom_headers_before_creating_client(self):
        with patch.dict(os.environ, {"OPENAI_CUSTOM_HEADERS":
                                     '{"Authorization":"Bearer private-header-value"}'}):
            with self.assertRaisesRegex(AgentError, "Unset OPENAI_CUSTOM_HEADERS"):
                self.run_soclaas(chat_sequence())
        self.constructor.assert_not_called()
        self.client.chat.completions.create.assert_not_called()
        self.assertNotIn("private-header-value", self.trace.read_text())
        self.assertEqual(self.read_trace()["status"], "failed")

    def test_unknown_provider_fails_before_request(self):
        with self.assertRaisesRegex(AgentError, "provider must"):
            run_agent([candidate()], "2026-10-01", 1, "chosen-model", self.trace, provider="unknown")
        self.constructor.assert_not_called()
        self.assertIn("ended_at", self.read_trace())

    def test_soclaas_malformed_no_call_and_truncated_responses_fail_closed(self):
        base = chat_sequence()[0]
        malformed = []
        for field, value in (("choices", []),):
            item = deepcopy(base)
            item[field] = value
            malformed.append(item)
        for finish_reason in ("length", "content_filter", None):
            item = deepcopy(base)
            item["choices"][0]["finish_reason"] = finish_reason
            malformed.append(item)
        for tool_calls in (None, [], [{"type": "function", "function": {"name": "list_candidates"}}]):
            item = deepcopy(base)
            item["choices"][0]["message"]["tool_calls"] = tool_calls
            malformed.append(item)
        item = deepcopy(base)
        item["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = {"query": ""}
        malformed.append(item)
        item = deepcopy(base)
        item["choices"][0]["message"]["refusal"] = "Request refused"
        malformed.append(item)
        for item in malformed:
            with self.subTest(item=item):
                with self.assertRaises(AgentError):
                    self.run_soclaas([item])
                trace = self.read_trace()
                self.assertEqual(trace["status"], "failed")
                self.assertIn("ended_at", trace)
                self.assertGreaterEqual(trace["elapsed_seconds"], 0)

    def test_soclaas_malformed_arguments_can_repair_without_skipping_forced_phase(self):
        bad = chat_response("list_candidates", {"query": ""})
        bad["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = "{broken"
        captured = []
        result = self.run_soclaas([bad] + chat_sequence(), captured)
        self.assertEqual(result["selected_ids"], ["income"])
        self.assertEqual(captured[0]["tool_choice"], captured[1]["tool_choice"])
        self.assertFalse(self.read_trace()["events"][0]["validation"]["accepted"])
        self.assertIn("error", json.loads(captured[1]["messages"][-1]["content"]))

    def test_soclaas_provider_cannot_ignore_a_forced_tool(self):
        captured = []
        premature = chat_response("submit_analysis", submission())
        self.run_soclaas([premature] + chat_sequence(), captured)
        trace = self.read_trace()
        self.assertIn("requires the list_candidates", trace["events"][0]["validation"]["error"])
        self.assertEqual(captured[1]["tool_choice"]["function"]["name"], "list_candidates")

    def test_soclaas_invalid_final_submission_exhausts_budget_without_fallback(self):
        invalid = submission()
        invalid["narratives"][0]["sales"] = "Prices may grow 30%."
        with self.assertRaisesRegex(AgentError, "turn budget.*no fallback"):
            self.run_soclaas(chat_sequence(invalid))
        self.assertEqual(self.client.chat.completions.create.call_count, 3)
        self.assertEqual(self.read_trace()["usage"]["requests"], 3)
        self.assertFalse(self.read_trace()["events"][-1]["validation"]["accepted"])

    def test_soclaas_errors_redact_both_provider_key_formats(self):
        exception = RuntimeError("clsk_test-secret clsk_other-private sk-other-secret")
        with self.assertRaises(AgentError) as raised:
            self.run_soclaas([exception])
        for secret in ("clsk_test-secret", "clsk_other-private", "sk-other-secret"):
            self.assertNotIn(secret, str(raised.exception))
            self.assertNotIn(secret, self.trace.read_text())
        self.assertEqual(self.read_trace()["usage"]["requests"], 1)
        self.assertEqual(self.read_trace()["provider"], "soclaas")

    def test_openai_records_returned_model_and_timing_without_chat_path(self):
        responses = sequence()
        responses[-1]["model"] = "actual-openai-snapshot"
        self.run_mock(responses)
        self.client.chat.completions.create.assert_not_called()
        trace = self.read_trace()
        self.assertEqual(trace["provider"], "openai")
        self.assertEqual(trace["api_mode"], "responses")
        self.assertEqual(trace["actual_model"], "actual-openai-snapshot")
        self.assertIn("ended_at", trace)
        self.assertGreaterEqual(trace["elapsed_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
