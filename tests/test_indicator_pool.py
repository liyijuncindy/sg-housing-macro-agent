"""Pool exports must distinguish observed evidence from editorial explanations."""
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest

from housing_agent.indicator_pool import build_indicator_pool, write_indicator_pool


ROOT = Path(__file__).resolve().parents[1]
FAMILY_REASON = ("Selected for economic-family coverage (financing_cost): highest data-quality score within this family, "
                 "with deterministic id tie-breaking. The family defaults to the theme when not specified.")


def candidate(number=0):
    return {"table_id": f"T{number}", "row_id": "1", "expected_name": "Configured name",
            "expected_unit": "Number", "frequency": "Q", "definition": "Configured definition",
            "scope": "Configured scope", "theme": "theme"}


def evaluation(number=0, **overrides):
    item = {"id": f"T{number}:1", "metadata": {"name": "Actual name", "definition": "Actual source definition",
            "frequency": "M", "unit": "Per Cent", "scope": "Actual scope", "source_provider": "Actual provider",
            "source_agency": "Actual agency", "source_url": "https://official.example/data.csv",
            "retrieved_at": "2026-10-01T10:00:00+08:00", "provenance": {"raw_file": "raw/data.csv", "raw_sha256": "a" * 64}},
            "latest": {"period": "2026-09", "value": 1.2336}, "quality": {"eligible": True, "score": 94,
            "reasons": [], "warnings": []}, "changes": []}
    item.update(overrides)
    return item


def run(**overrides):
    item = {"run_id": "current-run", "as_of": "2026-09-30", "created_at": "2026-10-01T02:00:00+00:00", "mode": "rules"}
    item.update(overrides)
    return item


def notes(number=0):
    return {f"T{number}:1": {"name_zh": "测试指标", "definition_zh": "配置中文定义", "rationale_zh": "候选经济机制说明",
            "caveat_zh": "覆盖范围限制", "source_agency": "Planned agency", "planned_source_url": "https://planned.example/table",
            "planned_source_label": "Planned provider"}}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.event_attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        for name, value in attrs:
            if tag == "a" and name == "href":
                self.links.append(value)
            if name.lower().startswith("on"):
                self.event_attributes.append((name, value))


class IndicatorPoolTests(unittest.TestCase):
    def build(self, item=None, selection=None, **kwargs):
        return build_indicator_pool(run(), [candidate()], [evaluation() if item is None else item],
                                    {"selected_ids": ["T0:1"], "decisions": [{"id": "T0:1", "reason": FAMILY_REASON}]} if selection is None else selection,
                                    notes=notes(), **kwargs)

    def test_actual_provider_definition_frequency_and_unit_override_planned(self):
        row = self.build()["rows"][0]
        self.assertEqual(row["source"]["url"], "https://official.example/data.csv")
        self.assertEqual(row["source"]["label"], "Actual provider")
        self.assertEqual(row["source"]["agency"], "Actual agency")
        self.assertEqual(row["source"]["kind"], "actual")
        self.assertEqual(row["definition"], "Actual source definition")
        self.assertIn("Actual source definition", row["definition_zh"])
        self.assertNotIn("配置中文定义", row["definition_zh"])
        self.assertEqual((row["frequency_zh"], row["unit_zh"], row["scope"]), ("月度", "%", "Actual scope"))

    def test_matching_definition_uses_reviewed_chinese_note(self):
        item = evaluation()
        item["metadata"]["definition"] = candidate()["definition"]
        self.assertEqual(self.build(item)["rows"][0]["definition_zh"], "配置中文定义")

    def test_failure_does_not_reuse_stale_latest_or_placeholder_zero_score(self):
        item = evaluation(metadata={"name": "Configured name"}, quality={"eligible": False, "score": 0,
                          "reasons": ["Source undergoing maintenance"], "warnings": []})
        row = self.build(item, {"selected_ids": []})["rows"][0]
        self.assertEqual(row["status"], "maintenance_unavailable")
        self.assertIsNone(row["latest"])
        self.assertIsNone(row["quality"]["score"])
        self.assertIsNone(row["quality"]["eligible"])
        self.assertFalse(row["quality_assessed"])
        self.assertNotIn("1.2336", row["data_status_zh"])
        self.assertNotIn("0/100", row["data_status_zh"])
        self.assertEqual(row["source"]["url"], "https://planned.example/table")
        self.assertEqual(row["source"]["status_label"], "配置来源，本次未获取")

    def test_generic_failure_is_not_assumed_to_be_maintenance(self):
        item = evaluation(metadata={}, quality={"eligible": False, "score": 0, "reasons": ["HTTP 502"]})
        self.assertEqual(self.build(item, {"selected_ids": []})["rows"][0]["status"], "unavailable")

    def test_captured_ineligible_and_eligible_unselected_are_distinct(self):
        item = evaluation(quality={"eligible": False, "score": 30, "reasons": ["Insufficient history"]})
        row = self.build(item, {"selected_ids": []})["rows"][0]
        self.assertEqual(row["status"], "ineligible")
        self.assertEqual(row["quality"]["score"], 30)
        row = self.build(selection={"selected_ids": []})["rows"][0]
        self.assertEqual(row["status"], "eligible_unselected")
        self.assertEqual(self.build(selection={})["rows"][0]["status"], "eligible_pending")

    def test_no_usable_observation_does_not_display_quality(self):
        for latest in (None, {"period": "2026-09", "value": None}, {"period": "2026-09", "value": True}):
            with self.subTest(latest=latest):
                row = self.build(evaluation(latest=latest), {"selected_ids": []})["rows"][0]
                self.assertEqual(row["status"], "no_usable_observation")
                self.assertIsNone(row["quality"]["score"])

    def test_preliminary_and_inconsistent_selection_are_explicit(self):
        row = self.build(evaluation(latest={"period": "2026-Q2", "value": 6605, "preliminary": True}))["rows"][0]
        self.assertIn("初步值（官方标记）", row["data_status_zh"])
        pool = self.build(evaluation(metadata={}))
        self.assertFalse(pool["rows"][0]["selected"])
        self.assertTrue(pool["rows"][0]["selection_record_selected"])
        self.assertTrue(pool["warnings"])

    def test_exact_reason_and_origin_preserved_without_model_relabelling(self):
        reason = "  Original reason\nwith a second line.  "
        for origin in ("model", "system", "rules"):
            with self.subTest(origin=origin):
                decision = {"id": "T0:1", "reason": reason, "reason_origin": origin}
                row = self.build(selection={"selected_ids": ["T0:1"], "decisions": [decision]})["rows"][0]
                self.assertEqual(row["decision_reason"], reason)
                self.assertEqual(row["original_decision"], decision)
                self.assertEqual(row["decision_reason_origin"], origin)
                if origin == "system":
                    self.assertIn("不能当作模型", row["selection_summary_zh"])

    def test_known_rule_reasons_have_concrete_chinese_explanation(self):
        row = self.build()["rows"][0]
        self.assertIn("优先补足类别覆盖", row["selection_summary_zh"])
        self.assertEqual(row["decision_reason"], FAMILY_REASON)
        fill = "Selected to fill remaining capacity by data-quality score after economic-family coverage; family: financing_cost."
        exclude = "Eligible but not selected: the requested capacity was reached after prioritizing economic-family coverage, quality score and deterministic id tie-breaking; family: financing_cost."
        for reason, selected, expected in ((fill, ["T0:1"], "补足剩余名额"), (exclude, [], "报告名额已满")):
            row = self.build(selection={"selected_ids": selected, "decisions": [{"id": "T0:1", "reason": reason}]})["rows"][0]
            self.assertIn(expected, row["selection_summary_zh"])
        for reason in (None, "Selected because my own criteria differ"):
            row = self.build(selection={"selected_ids": ["T0:1"], "decisions": [{"id": "T0:1", "reason": reason}]})["rows"][0]
            self.assertNotIn("补足类别覆盖", row["selection_summary_zh"])
        row = self.build(selection={"selected_ids": ["T0:1"], "decisions": [{"id": "T0:1", "reason": FAMILY_REASON, "reason_origin": "model"}]})["rows"][0]
        self.assertNotIn("补足类别覆盖", row["selection_summary_zh"])

    def test_full_twelve_candidates_keep_catalogue_order_without_evaluations(self):
        catalogue = [candidate(number) for number in range(12)]
        pool = build_indicator_pool(run(), catalogue, [], {"selected_ids": []}, notes={})
        self.assertEqual([row["id"] for row in pool["rows"]], [f"T{number}:1" for number in range(12)])
        self.assertEqual(pool["counts"]["candidates"], 12)
        self.assertTrue(all(row["latest"] is None for row in pool["rows"]))
        self.assertTrue(all(row["source"]["kind"] == "configured_only" for row in pool["rows"]))

    def test_snapshot_capture_range_uses_actual_times_with_timezone(self):
        early, late = evaluation(0), evaluation(1)
        early["metadata"]["retrieved_at"] = "2026-10-01T08:00:00+08:00"
        late["metadata"]["retrieved_at"] = "2026-10-01T01:00:00Z"
        pool = build_indicator_pool(run(source_run={"name": "original-snapshot"}), [candidate(0), candidate(1)], [late, early], {"selected_ids": []}, notes={})
        self.assertEqual(pool["source_capture"]["min"], early["metadata"]["retrieved_at"])
        self.assertEqual(pool["source_capture"]["max"], late["metadata"]["retrieved_at"])
        self.assertEqual(pool["source_run_id"], "original-snapshot")
        self.assertTrue(pool["snapshot_reused"])
        self.assertIn("没有重新取数", pool["source_capture_note"])

    def test_notes_embedded_copied_and_content_hash_changes(self):
        provided = notes()
        pool = build_indicator_pool(run(), [candidate()], [], {}, notes=provided)
        self.assertEqual(pool["notes"], provided)
        provided["T0:1"]["name_zh"] = "Changed"
        changed = build_indicator_pool(run(), [candidate()], [], {}, notes=provided)
        self.assertNotEqual(pool["notes_sha256"], changed["notes_sha256"])
        self.assertEqual(pool["notes"]["T0:1"]["name_zh"], "测试指标")

    def test_write_three_formats_and_export_disclosure(self):
        pool = self.build()
        pool["export_provenance"] = {"exported_at": "2026-10-02T03:00:00Z", "network_calls": 0, "model_calls": 0}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_indicator_pool(path, pool)
            self.assertEqual(json.loads((path / "indicator_pool.json").read_text()), pool)
            for suffix in ("md", "html"):
                output = (path / ("indicator_pool." + suffix)).read_text()
                self.assertIn("依据已保存运行导出；未刷新数据、未重新筛选、未调用模型", output)
                self.assertIn("原运行报告生成时间", output)
                self.assertIn("2026-10-02T03:00:00Z", output)
            markdown = (path / "indicator_pool.md").read_text()
            self.assertIn("| 指标 | 口径与频率 |", markdown)
            page = (path / "indicator_pool.html").read_text()
            self.assertIn('<table>', page)
            self.assertIn('id="search"', page)
            self.assertIn('id="status"', page)

    def test_html_escapes_injected_text_and_rejects_unsafe_links(self):
        for unsafe in ('javascript:alert(1)', 'data:text/html,<script>alert(1)</script>', 'https://user:pass@example.com', 'https://example.com/\nnext'):
            with self.subTest(unsafe=unsafe):
                malicious = '</script><script>alert(1)</script><img src=x onerror="alert(1)">'
                item = evaluation()
                item["metadata"]["source_url"] = unsafe
                item["metadata"]["definition"] = malicious
                decision = {"id": "T0:1", "reason": malicious, "reason_origin": "model"}
                editorial = notes()
                editorial["T0:1"]["name_zh"] = malicious
                pool = build_indicator_pool(run(), [candidate()], [item], {"selected_ids": ["T0:1"], "decisions": [decision]}, notes=editorial)
                with tempfile.TemporaryDirectory() as directory:
                    write_indicator_pool(Path(directory), pool)
                    page = (Path(directory) / "indicator_pool.html").read_text()
                    parser = PageParser()
                    parser.feed(page)
                    self.assertEqual(parser.tags.count("script"), 1)
                    self.assertNotIn("img", parser.tags)
                    self.assertFalse(parser.event_attributes)
                    self.assertFalse(parser.links)
                    self.assertIn("&lt;script&gt;", page)
                    self.assertEqual(pool["rows"][0]["decision_reason"], malicious)

    def test_real_saved_run_has_three_actual_and_nine_missing_without_old_values(self):
        directory = ROOT / "examples" / "independent_sources_run"
        data = {name: json.loads((directory / (name + ".json")).read_text()) for name in ("report_context", "catalogue", "evaluations", "selection")}
        pool = build_indicator_pool(data["report_context"], data["catalogue"], data["evaluations"], data["selection"])
        self.assertEqual(pool["counts"]["candidates"], 12)
        self.assertEqual(pool["counts"]["selected"], 3)
        captured = [row for row in pool["rows"] if row["has_provenance"]]
        missing = [row for row in pool["rows"] if not row["has_provenance"]]
        self.assertEqual((len(captured), len(missing)), (3, 9))
        self.assertTrue(all(row["status"] == "maintenance_unavailable" for row in missing))
        self.assertTrue(all(row["latest"] is None and row["quality"]["score"] is None for row in missing))
        self.assertEqual({row["id"] for row in captured}, {"M700071:23", "M182342:2", "M184101:1"})
        self.assertEqual(len(pool["notes"]), 12)

    def test_duplicate_catalogue_or_evaluation_ids_rejected(self):
        with self.assertRaises(ValueError):
            build_indicator_pool(run(), [candidate(), candidate()], [], {}, notes={})
        with self.assertRaises(ValueError):
            build_indicator_pool(run(), [candidate()], [evaluation(), evaluation()], {}, notes={})


if __name__ == "__main__":
    unittest.main()
