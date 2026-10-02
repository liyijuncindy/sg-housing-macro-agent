"""Editorial corrections retain immutable evidence and explicit authorship."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from housing_agent.review import review_report
from housing_agent.pipeline import replay
from housing_agent.storage import sha256_bytes, write_json
from tests import test_report_v2 as fixtures


class EditorialReviewTests(unittest.TestCase):
    def setup_review(self, root):
        fixtures.ReportV2IntegrationTests().setup_run(root)
        review={"summary":"Clarified candidate scope.","decision_edits":{"M400391:2":"This is total pipeline, not an unsold subset."},
                "narrative_edits":{},"notes":["Source definitions support this correction."]}
        write_json(root/"review.json",review)
        return review

    def test_offline_review_preserves_selection_evidence_and_exact_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.setup_review(root)
            before=(root/"run/manifest.json").read_bytes()
            selected=json.loads((root/"run/selection.json").read_text())
            with patch("housing_agent.pipeline.SingStatClient",side_effect=AssertionError("No network")),patch("housing_agent.charts.write_charts",side_effect=AssertionError("Do not regenerate charts")):
                result=review_report(root/"run",root/"review.json",root/"reviewed")
            self.assertEqual((root/"run/manifest.json").read_bytes(),before)
            new=json.loads((root/"reviewed/selection.json").read_text())
            self.assertEqual(new["selected_ids"],selected["selected_ids"])
            self.assertEqual(json.loads((root/"reviewed/original_selection.json").read_text()),selected)
            decision=next(d for d in new["decisions"] if d["id"]=="M400391:2")
            self.assertEqual(decision["reason_origin"],"editorial_review")
            self.assertIn("editorial_review",(root/"reviewed/report.md").read_text())
            for name in ("normalized.json","evaluations.json","research.json","charts/test.svg"):
                self.assertEqual((root/"reviewed"/name).read_bytes(),(root/"run"/name).read_bytes())
            self.assertEqual(result["model_calls"],0);self.assertEqual(result["network_calls"],0)
            self.assertEqual(result["usage"]["total_tokens"],0)
            self.assertEqual(result["report_fields_version"],2)
            self.assertEqual(result["editorial_review"]["narrative_edits"],0)
            self.assertEqual(result["source_execution"]["manifest_sha256"],sha256_bytes(before))
            self.assertEqual(replay(root/"reviewed",root/"replayed.md")["model_calls"],0)

    def test_changed_source_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.setup_review(root);(root/"run/research.json").write_text("{}")
            with self.assertRaisesRegex(ValueError,"Missing or changed"):
                review_report(root/"run",root/"review.json",root/"bad")
            self.assertFalse((root/"bad").exists())

    def test_unknown_candidate_edit_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.setup_review(root);r["decision_edits"]={"invented":"Wrong candidate"}
            write_json(root/"review.json",r)
            with self.assertRaisesRegex(ValueError,"unknown candidate"):
                review_report(root/"run",root/"review.json",root/"bad")
            self.assertFalse((root/"bad").exists())

    def test_review_cannot_change_narrative_evidence_or_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);r=self.setup_review(root)
            selected=json.loads((root/"run/selection.json").read_text())["selected_ids"][0]
            r["narrative_edits"]={selected:{"evidence_ids":["invented"]}}
            write_json(root/"review.json",r)
            with self.assertRaisesRegex(ValueError,"unsupported field"):
                review_report(root/"run",root/"review.json",root/"bad")
            self.assertFalse((root/"bad").exists())


if __name__=="__main__":unittest.main()
