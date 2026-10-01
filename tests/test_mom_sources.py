"""Offline parser/adapter regressions model the verified public MOM files."""
from copy import deepcopy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock
import xml.etree.ElementTree as ET
import zipfile

from housing_agent.mom_sources import (INCOME_URL, UNEMPLOYMENT_URL, fetch_mom_series,
                                       parse_income_xlsx, parse_unemployment_csv)
from housing_agent.sources import SourceError

# These field names and sample rows were captured from the official CSV.
HEADER = ('period,quarter_annual,residential_status,seasonally_adjusted_unemployment_rate,'
          'non-seasonally_adjusted_unemployment_rate,seasonally_adjusted_unemployed_num,'
          'non-seasonally_adjusted_unemployed_num,annual_avg_unemployment_rate,annual_avg_unemployed_num\r\n')
CSV = (HEADER + '1992-03,quarter,resident,2.2,1.8,30900,25600,,\r\n'
       '2026-06,quarter,resident,2.9,3.0,71000,72000,,\r\n'
       '2025,annual,resident,,,,,2.8,68400\r\n').encode()
TITLE = 'Mean Gross Monthly Income From Employment (Including Employer/Platform Operator CPF contributions and Excluding Bonus) of Employed Residents'
NOTES = [
    '1. Residents refer to Singapore Citizens and Permanent Residents.',
    '2. Gross monthly income refers to income earned from employment. For self-employed persons, income is before deduction of income tax and platform workers’ share of CPF contributions.',
    '3. Data are for all employed persons excluding full-time National Servicemen.',
    '4. Compare with the same quarter of prior years; the mean can be skewed by high earners.',
    '5. p: preliminary.',
]
LEVELS = [5328, 5495, 5558, 5602, 5752, 5779, 5759, 5680, 5750, 5863, 6027,
          6090, 6107, 6138, 6113, 6282, 6390, 6429, 6442, 6593, 6605]
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def workbook(title=TITLE, unit='Dollars', notes=None, mutate=None, target='worksheets/sheet1.xml'):
    """Small standard OOXML file with the same header/value/note geometry as MOM."""
    book = f'<workbook xmlns="{NS}" xmlns:r="{REL}"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    relationships = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     f'<Relationship Id="rId1" Target="{target}" Type="{REL}/worksheet"/></Relationships>')
    shared = ET.Element('sst', xmlns=NS)
    strings = []
    def shared_index(value):
        strings.append(value)
        item = ET.SubElement(shared, 'si')
        ET.SubElement(item, 't').text = value
        return str(len(strings) - 1)
    sheet = ET.Element('worksheet', xmlns=NS)
    data = ET.SubElement(sheet, 'sheetData')
    rows = {}
    def cell(address, value, text=False):
        number = ''.join(c for c in address if c.isdigit())
        if number not in rows:
            rows[number] = ET.SubElement(data, 'row', r=number)
        item = ET.SubElement(rows[number], 'c', r=address, **({'t': 's'} if text else {}))
        ET.SubElement(item, 'v').text = shared_index(value) if text else str(value)
    cell('A2', title, True)
    cell('U4', unit, True)
    for index, level in enumerate(LEVELS):
        ordinal = 2021 * 4 + 1 + index
        year, quarter0 = divmod(ordinal, 4)
        column = chr(ord('A') + index)
        cell(column + '5', f'{quarter0 + 1}Q {year}' + ('p' if index == 20 else ''), True)
        cell(column + '6', level)
    cell('U7', 'Source: Labour Force Survey, Manpower Research and Statistics Department, MOM', True)
    cell('A9', 'Notes:', True)
    for index, note in enumerate(NOTES if notes is None else notes):
        cell(f'A{10 + index}', note, True)
    if mutate:
        mutate(sheet, shared)
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('xl/workbook.xml', book)
        archive.writestr('xl/_rels/workbook.xml.rels', relationships)
        archive.writestr('xl/sharedStrings.xml', ET.tostring(shared))
        archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(sheet))
    return result.getvalue()


class MomParserTests(unittest.TestCase):
    def test_csv_filters_annual_and_nonresident_rows_and_preserves_csv_precision(self):
        data = CSV + b'2026-06,quarter,citizen,3.1,3.2,100,100,,\r\n'
        observations = parse_unemployment_csv(data)
        self.assertEqual([row['period'] for row in observations], ['1992-Q1', '2026-Q2'])
        self.assertEqual(observations[-1]['value'], 2.9)
        self.assertEqual(observations[-1]['raw_value'], '2.9')
        self.assertEqual(observations[-1]['raw_index'], 1)
        self.assertEqual(observations[-1]['raw_locator'], 'CSV row 3, column seasonally_adjusted_unemployment_rate')
        self.assertTrue(all('published_at' not in row for row in observations))

    def test_csv_definition_and_period_changes_fail(self):
        for body in [CSV.replace(b'seasonally_adjusted_unemployment_rate,', b'rate,', 1),
                     CSV.replace(b'2026-06', b'2026-05'),
                     CSV.replace(b'2.9,3.0', b'not-a-number,3.0'),
                     CSV.replace(b'2.9,3.0', b'2900,3.0'),
                     CSV + b'2026-06,quarter,resident,2.9,3.0,100,100,,\r\n']:
            with self.subTest(body=body):
                with self.assertRaises(SourceError):
                    parse_unemployment_csv(body)

    def test_csv_missing_value_is_explicit_and_empty_selection_is_rejected(self):
        rows = parse_unemployment_csv(CSV.replace(b'2.9,3.0', b',3.0'))
        self.assertIsNone(rows[-1]['value'])
        with self.assertRaises(SourceError):
            parse_unemployment_csv(HEADER.encode())

    def test_income_geometry_preliminary_markers_and_official_definition(self):
        observations, metadata = parse_income_xlsx(workbook())
        self.assertEqual(len(observations), 21)
        self.assertEqual([o['value'] for o in observations], LEVELS)
        self.assertEqual(observations[0]['period'], '2021-Q2')
        latest = observations[-1]
        self.assertEqual(latest['period'], '2026-Q2')
        self.assertEqual(latest['raw_period'], '2Q 2026p')
        self.assertEqual(latest['raw_locator'], 'Sheet1!U6 (period Sheet1!U5)')
        self.assertTrue(latest['preliminary'])
        self.assertFalse(observations[-2]['preliminary'])
        self.assertIn('Platform Operator CPF', metadata['official_title'])
        self.assertIn('5. p: preliminary.', metadata['notes'])
        self.assertIn('Sheet1!A14', metadata['note_locators'])

    def test_income_definition_unit_or_required_notes_cannot_silently_drift(self):
        for body in [workbook(title=TITLE.replace('Excluding Bonus', 'Including Bonus')),
                     workbook(title=TITLE.replace('Employer/Platform Operator CPF', 'Employer CPF')),
                     workbook(unit='Thousand Dollars'), workbook(notes=NOTES[:-1])]:
            with self.subTest():
                with self.assertRaises(SourceError):
                    parse_income_xlsx(body)

    def test_income_formula_cached_result_is_rejected(self):
        def add_formula(sheet, shared):
            cell = next(item for item in sheet.iter('c') if item.get('r') == 'U6')
            ET.SubElement(cell, 'f').text = 'A6+1277'
        with self.assertRaisesRegex(SourceError, 'formulas'):
            parse_income_xlsx(workbook(mutate=add_formula))

    def test_income_missing_value_cell_and_unmatched_values_are_rejected(self):
        def remove_value(sheet, shared):
            for row in sheet.iter('row'):
                for cell in list(row):
                    if cell.get('r') == 'U6':
                        row.remove(cell)
        def orphan_value(sheet, shared):
            row = next(row for row in sheet.iter('row') if row.get('r') == '6')
            cell = ET.SubElement(row, 'c', r='V6')
            ET.SubElement(cell, 'v').text = '9999'
        for mutate in (remove_value, orphan_value):
            with self.subTest():
                with self.assertRaises(SourceError):
                    parse_income_xlsx(workbook(mutate=mutate))

    def test_income_wrong_zip_or_worksheet_relationship_is_rejected(self):
        for body in [b'<html>Maintenance</html>', workbook(target='../unknown.xml')]:
            with self.subTest():
                with self.assertRaises(SourceError):
                    parse_income_xlsx(body)

    def test_income_duplicate_quarter_is_rejected(self):
        def duplicate_period(sheet, shared):
            cell = next(item for item in sheet.iter('c') if item.get('r') == 'U5')
            previous = next(item for item in sheet.iter('c') if item.get('r') == 'T5')
            cell.find('v').text = previous.find('v').text
        with self.assertRaisesRegex(SourceError, 'Duplicate'):
            parse_income_xlsx(workbook(mutate=duplicate_period))


class MomAdapterTests(unittest.TestCase):
    def spec(self, identifier):
        catalogue = json.loads((Path(__file__).parents[1] / 'housing_agent/data/catalogue.json').read_text())
        return deepcopy(next(spec for spec in catalogue if f"{spec['table_id']}:{spec['row_id']}" == identifier))

    def client(self, body, url):
        client = Mock()
        client.download.return_value = (body, {'url': url, 'raw_file': 'raw/download',
            'raw_sha256': 'recorded-download-hash', 'retrieved_at': '2026-10-01T00:00:00Z'})
        client.metadata.return_value = {'raw_file': 'raw/metadata.json', 'raw_sha256': 'recorded-metadata-hash'}
        return client

    def test_income_download_maps_identity_but_retains_publisher_label_and_notes(self):
        client = self.client(workbook(), INCOME_URL)
        series = fetch_mom_series(client, self.spec('M184101:1'))
        client.download.assert_called_once_with(INCOME_URL, name='mom_mean_employment_income', suffix='.xlsx')
        self.assertEqual(series['id'], 'M184101:1')
        self.assertEqual(series['name'], TITLE)
        self.assertEqual(series['source_provider'], 'MOM official XLSX')
        self.assertIn('platform operator CPF', series['definition'])
        self.assertIn('p: preliminary', series['source_footnote'])
        self.assertEqual(series['comparisons'], ['year_on_year'])
        self.assertTrue(series['observations'][-1]['preliminary'])
        self.assertEqual(series['provenance']['raw_sha256'], 'recorded-download-hash')
        metadata = client.metadata.call_args.args[1]
        self.assertIn('not official API metadata', metadata['metadata_origin'])
        self.assertIn('Platform Operator CPF', metadata['official_title'])

    def test_unemployment_download_selects_sa_rate_and_discloses_missing_release_dates(self):
        client = self.client(CSV, UNEMPLOYMENT_URL)
        series = fetch_mom_series(client, self.spec('M182342:2'))
        client.download.assert_called_once_with(UNEMPLOYMENT_URL, name='mom_resident_unemployment', suffix='.csv')
        self.assertEqual(series['seasonal_adjustment'], 'Seasonally Adjusted')
        self.assertEqual(series['source_provider'], 'MOM official CSV')
        self.assertEqual(series['observations'][-1]['value'], 2.9)
        metadata = client.metadata.call_args.args[1]
        self.assertEqual(metadata['selected_filters'], {'quarter_annual': 'quarter', 'residential_status': 'resident'})
        self.assertIn('none are inferred', metadata['notes'])

    def test_wrong_mapping_is_rejected_without_downloading(self):
        changes = {'expected_name': 'Different concept with the same ID', 'expected_unit': 'Index',
                   'frequency': 'M', 'change_kind': 'absolute', 'seasonal_adjustment': 'Changed adjustment',
                   'comparisons': ['previous_period'], 'reference_month_day': '06-30'}
        for identifier in ('M182342:2', 'M184101:1'):
            for field, value in changes.items():
                with self.subTest(identifier=identifier, field=field):
                    client = Mock()
                    spec = self.spec(identifier)
                    spec[field] = value
                    with self.assertRaisesRegex(SourceError, field):
                        fetch_mom_series(client, spec)
                    client.download.assert_not_called()
                    client.metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
