"""Readable English reports, safe local chart embedding and old-run replay."""
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from housing_agent.agent import _validate_submission
from housing_agent.english_pool import build_english_pool, write_english_pool
from housing_agent.report import render_report, render_html
from housing_agent.pipeline import run_workflow, replay
from housing_agent.storage import write_json, sha256_bytes
from tests.test_agent import candidate, submission


ROOT=Path(__file__).resolve().parents[1]


def fixture(client,spec):
    key=f"{spec['table_id']}:{spec['row_id']}"
    filename=key.replace(':','_').replace('.','_')
    raw=f"raw/{filename}.json";meta=f"raw/{filename}_meta.json"
    write_json(client.run_dir/raw,{'fixture':key})
    write_json(client.run_dir/meta,{'metadata':'Synthetic only'})
    frequency=spec['frequency']
    if frequency=='A':
        periods=[str(y) for y in range(2015,2026)]
    elif frequency=='Q':
        periods=[f'{y}-Q{q}' for y in range(2015,2027) for q in range(1,5) if (y,q)<=(2026,2)]
    else:
        periods=[f'{y}-{m:02}' for y in range(2015,2027) for m in range(1,13) if (y,m)<=(2026,8)]
    return {'id':key,'name':spec['expected_name'],'table_id':spec['table_id'],'row_id':spec['row_id'],
            'unit':spec['expected_unit'],'frequency':frequency,'theme':spec['theme'],'selection_family':spec['selection_family'],
            'definition':spec['definition'],'scope':spec['scope'],'mechanism':spec['mechanism'],'change_kind':spec['change_kind'],
            'update_frequency':spec['update_frequency'],'source_url':f"https://tablebuilder.singstat.gov.sg/table/TS/{spec['table_id']}",
            'source_agency':'Synthetic fixture','retrieved_at':'2026-10-01T00:00:00+00:00','source_updated_at':'test',
            'provenance':{'raw_file':raw,'metadata_file':meta,'raw_sha256':sha256_bytes((client.run_dir/raw).read_bytes()),'metadata_sha256':sha256_bytes((client.run_dir/meta).read_bytes())},
            'observations':[{'period':p,'value':100+i,'raw_period':p,'raw_value':str(100+i),'raw_index':i} for i,p in enumerate(periods)]}


def charts(output,research,evaluations,selection):
    p=output/'charts';p.mkdir()
    (p/'test.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><text x="0" y="15">Test chart</text></svg>')
    return [{'path':'charts/test.svg','title':'Synthetic chart','caption':'Synthetic only'}]


class CompleteEnglishDecisionTests(unittest.TestCase):
    def test_missing_exclusion_is_rejected_in_full_report_mode(self):
        data={'income':candidate(),'hdb':candidate('hdb')}
        with self.assertRaisesRegex(ValueError,'missing IDs.*hdb'):
            _validate_submission(submission(),data,set(data),2,require_complete_decisions=True)
        old=_validate_submission(submission(),data,set(data),2)
        self.assertEqual(old['decisions'][1]['reason_origin'],'system')

    def test_uninspected_exclusion_cannot_be_guessed(self):
        s=submission();s['decisions'].append({'id':'hdb','selected':False,'reason':'Capacity prioritises the retained channels.'})
        with self.assertRaisesRegex(ValueError,'must be inspected'):
            _validate_submission(s,{'income':candidate(),'hdb':candidate('hdb')},{'income'},2,require_complete_decisions=True)

    def test_complete_english_model_reasons_are_retained(self):
        s=submission();s['decisions'].append({'id':'hdb','selected':False,'reason':'Capacity prioritises the retained channels.'})
        result=_validate_submission(s,{'income':candidate(),'hdb':candidate('hdb')},{'income','hdb'},2,require_complete_decisions=True)
        self.assertTrue(all(d['reason_origin']=='model' for d in result['decisions']))

    def test_non_english_prose_is_rejected_for_new_report(self):
        s=submission();s['decisions'][0]['reason']='收入可影响购买能力。'
        with self.assertRaisesRegex(ValueError,'English'):
            _validate_submission(s,{'income':candidate()},{'income'},1,require_complete_decisions=True)


class ReportV2IntegrationTests(unittest.TestCase):
    def setup_run(self,root):
        with patch('housing_agent.pipeline.SingStatClient.discover',return_value=[]),patch('housing_agent.pipeline.fetch_series',side_effect=fixture),patch('housing_agent.charts.require_chart_dependencies'),patch('housing_agent.charts.write_charts',side_effect=charts):
            return run_workflow('2026-10-01',root/'run',report_version=2,source_policy='singstat',progress=lambda _:None)

    def test_complete_workflow_english_outcomes_research_and_rendered_charts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=self.setup_run(root)
            self.assertEqual(run['outcome_coverage']['downloaded'],3)
            self.assertEqual(run['research']['summary']['comparison_count'],48)
            md=(root/'run/report.md').read_text();page=(root/'run/report.html').read_text()
            self.assertIn('## Executive summary',md);self.assertIn('## Market outcomes',md)
            self.assertIn('Walk-forward prediction checks',md);self.assertIn('Vacancy with its denominator',md)
            self.assertIn('<table>',page);self.assertIn('data:image/svg+xml;base64,',page)
            for name in ('report.md','report.html','indicator_pool.md','indicator_pool.html','indicator_pool.json'):
                self.assertFalse(re.search(r'[\u3400-\u9fff]',(root/'run'/name).read_text()),name)
            result=replay(root/'run',root/'replayed.md')
            self.assertEqual(result['model_calls'],0)
            self.assertEqual((root/'replayed.md').read_bytes(),(root/'run/report.md').read_bytes())

    def test_saved_v2_recalculates_outcomes_without_data_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.setup_run(root)
            with patch('housing_agent.pipeline.SingStatClient',side_effect=AssertionError('No network')),patch('housing_agent.charts.require_chart_dependencies'),patch('housing_agent.charts.write_charts',side_effect=charts):
                result=run_workflow('2026-10-01',root/'saved',report_version=2,source_run=root/'run',progress=lambda _:None)
            self.assertFalse(result['outcome_coverage']['freshly_retrieved'])
            self.assertEqual(result['outcome_coverage']['downloaded'],3)
            self.assertEqual((root/'saved/outcomes_normalized.json').read_bytes(),(root/'run/outcomes_normalized.json').read_bytes())
            self.assertTrue(all(not r['attempts'] for r in json.loads((root/'saved/outcomes_source_routes.json').read_text())))

    def test_legacy_snapshot_cannot_silently_refresh_missing_outcomes(self):
        with tempfile.TemporaryDirectory() as tmp,patch('housing_agent.charts.require_chart_dependencies'),patch('housing_agent.pipeline.SingStatClient',side_effect=AssertionError('No network')):
            output=Path(tmp)/'new'
            with self.assertRaisesRegex(ValueError,'requires housing outcomes'):
                run_workflow('2026-10-01',output,report_version=2,source_run=ROOT/'examples/siliconflow_glm_reviewed_run',progress=lambda _:None)
            self.assertFalse(output.exists())

    def test_malformed_saved_outcome_catalogue_fails_before_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.setup_run(root)
            p=root/'run/outcomes_catalogue.json';p.write_text('[]')
            with patch('housing_agent.charts.require_chart_dependencies'),patch('housing_agent.agent.run_agent',side_effect=AssertionError('No paid call')):
                with self.assertRaisesRegex(ValueError,'Missing or changed'):
                    run_workflow('2026-10-01',root/'bad',report_version=2,source_run=root/'run',progress=lambda _:None)

    def test_html_escapes_source_text_and_rejects_external_or_traversing_images(self):
        md='<!-- housing-report-version: 2 -->\n# Report\n\n<script>alert(1)</script>\n\n![Unsafe](../secret.svg)\n\n![Remote](https://example.test/chart.svg)\n\n[Unsafe](javascript:alert)'
        page=render_html(md)
        self.assertNotIn('<script>',page);self.assertNotIn('javascript:',page)
        self.assertNotIn('src="../',page);self.assertNotIn('src="https:',page)

    def test_embedding_refuses_symlink_outside_asset_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'assets').mkdir();(root/'private.svg').write_text('<svg>private</svg>')
            (root/'assets/link.svg').symlink_to(root/'private.svg')
            md='<!-- housing-report-version: 2 -->\n# Report\n\n![Unsafe](link.svg)'
            page=render_html(md,asset_root=root/'assets')
            self.assertNotIn('base64',page)


if __name__=='__main__':unittest.main()
