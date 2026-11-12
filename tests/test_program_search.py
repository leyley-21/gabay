"""Direct education searches, retired-school cleanup and sourced salary behavior."""
import csv,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_application as fixtures
from app.db import database_connection
from app.schema import initialize_database
from app.services.location import locate_province
from app.services.catalog import import_references
from app.services.salary import prepare_salary
from app.config import REFERENCE_DIR

def csv_rows(name):
    with (REFERENCE_DIR/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

class DirectStudyTests(unittest.TestCase):
    setUp=fixtures.ApplicationTests.setUp
    tearDown=fixtures.ApplicationTests.tearDown
    def test_study_modal_and_school_search_endpoints_removed(self):
        body=self.client.get('/').data
        self.assertNotIn(b'program-search-dialog',body)
        self.assertNotIn(b'study-location-bar',body)
        self.assertEqual(self.client.post('/api/program-search',json={}).status_code,404)
        self.assertEqual(self.client.get('/api/program-catalog').status_code,404)
    def test_retired_tables_removed_and_history_preserved(self):
        self.client.post('/predict',json=self.profile)
        with database_connection(self.path) as db:
            db.execute('CREATE TABLE school_campuses (school TEXT)');db.execute("INSERT INTO school_campuses VALUES ('retired seed')")
            db.execute('CREATE TABLE school_programs (program TEXT)')
            db.execute('CREATE TABLE program_catalog (name TEXT)')
            db.execute('CREATE TABLE discovery_cache (data TEXT)')
        initialize_database(self.path)
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM quiz_attempts').fetchone()[0],1)
            for table in ('school_campuses','school_programs','program_catalog','discovery_cache'):
                self.assertIsNone(db.execute('SELECT name FROM sqlite_master WHERE name=?',(table,)).fetchone())
    def test_suggested_programs_still_come_from_the_existing_mappings(self):
        r=self.client.post('/predict',json={**self.profile,'goal':'Continue to College / Higher Ed'}).json
        for item in r['recommendations']:
            self.assertEqual([p['name'] for p in item['college_options']],[p.strip() for p in item['college_majors'].split('|') if p.strip()])
            self.assertEqual([p['name'] for p in item['tesda_options']],[p.strip() for p in item['tech_voc'].split('|') if p.strip()])
    def test_tesda_complete_list_and_active_catalog(self):
        rows=csv_rows('tesda_official_programs.csv')
        self.assertEqual(len(rows),659)
        self.assertEqual({r['list_type'] for r in rows},{'Training Regulations','Competency Standards'})
        self.assertTrue(any(r['list_status']=='superseded' for r in rows))
        active=[r for r in csv_rows('program_catalog.csv') if r['kind']=='tesda']
        self.assertEqual(len(active),597)
        self.assertTrue(any(r['name']=='Cookery NC II' for r in active))
        self.assertTrue(any(r['name']=='Digital Caregiving' for r in active))
    def test_expanded_college_catalog_covers_every_career_with_sourced_names(self):
        catalog=csv_rows('college_program_catalog.csv')
        self.assertGreater(len(catalog),1000)
        self.assertEqual({r['source_status'] for r in catalog},{'official_listed','classification_listed'})
        names={r['name'] for r in catalog}
        occupations={r['onet_code'] for r in csv_rows('occupation_catalog.csv')}
        mappings=csv_rows('college_programs.csv')
        self.assertEqual({r['onet_code'] for r in mappings},occupations)
        for row in mappings:
            self.assertTrue(row['programs'])
            for name in row['programs'].split(' | '):self.assertIn(name,names)
        by_title={r['occupation_title']:r['programs'] for r in mappings}
        self.assertIn('Forensic Science',by_title['Coroners'])
        self.assertIn('Nursing',by_title['Acute Care Nurses'])
        self.assertNotIn('Criminology',by_title['Information Security Analysts'])
        self.assertIn('Materials Engineering',by_title['Materials Engineers'])
    def test_fit_explanation_is_grounded_and_never_discloses_scores(self):
        from app.recommendation.explanations import build_fit_evidence, build_fit_cautions
        from app.config import RIASEC_COLUMNS
        row = dict(zip(RIASEC_COLUMNS, [2,6,5,2,2,4]))
        row.update(description='Develop software for medical equipment. Design visual interfaces.', is_wfh_capable=True)
        scores=dict.fromkeys('RIASEC',5)
        evidence=build_fit_evidence(row,scores,['Programming and coding','Bookkeeping'])
        self.assertTrue(evidence)
        for entry in evidence:
            self.assertIn(entry['task'], row['description'])
            self.assertEqual(entry['explanation'],'')
            self.assertEqual(entry['heading'],'')
            self.assertEqual(entry['source'],'O*NET occupation description')
            self.assertEqual(entry['connections'],[])
            self.assertNotIn('/5',entry['explanation'])
            self.assertNotIn('Bookkeeping',entry['explanation'])
        self.assertEqual(' '.join(e['task'] for e in evidence),row['description'])
        self.assertEqual(evidence,build_fit_evidence(row,dict.fromkeys('RIASEC',1),[]))
        self.assertEqual(build_fit_cautions(row,scores,'Work From Home'),[])
        row['description']='Test scientific instruments in a laboratory.'
        self.assertNotEqual(evidence[0]['task'],build_fit_evidence(row,scores,[])[0]['task'])

    def test_expanded_paths_use_existing_programs_and_role_specific_training(self):
        rows=csv_rows('college_programs.csv');college={r['occupation_title']:r['programs'] for r in rows}
        tesda={r['occupation_title']:r['qualifications'] for r in csv_rows('tesda_programs.csv')}
        self.assertIn('Computer Engineering',college['Software Developers'])
        self.assertIn('Programming (JAVA) NC III',tesda['Software Developers'])
        self.assertIn('Web Development NC III',tesda['Web Developers'])
        self.assertNotIn('Computer Systems Servicing',tesda['Software Developers'])
        self.assertEqual(tesda['Chief Executives'],'')
        self.assertNotIn('Contact Center',tesda['Advertising and Promotions Managers'])
        lookup={(r['kind'],r['name']) for r in csv_rows('program_catalog.csv')}
        for r in csv_rows('career_pathway_audit.csv'):
            self.assertIn((r['kind'],r['program_name']),lookup)
            self.assertTrue(r['source_url'].startswith('https://'))

    def test_all_catalog_fit_explanations_and_remote_guidance(self):
        from app.recommendation.explanations import build_fit_evidence
        from app.services.work_arrangements import work_arrangement
        for row in csv_rows('occupation_catalog.csv'):
            evidence=build_fit_evidence(row,dict.fromkeys('RIASEC',3),[])
            self.assertTrue(evidence,row['title'])
            self.assertTrue(all(e['task'] in row['description'] for e in evidence))
            self.assertEqual(' '.join(e['task'] for e in evidence),' '.join(row['description'].split()))
            self.assertTrue(all(not e['explanation'] for e in evidence))
            text=' '.join(e['explanation'] for e in evidence)
            self.assertNotIn('/5',text)
            self.assertNotRegex(text,r'\b(?:exam|score|rated|rating)\b')
            row['is_wfh_capable']=row['is_wfh_capable'].lower()=='true'
            guidance=work_arrangement(row)
            self.assertNotIn('No degree',guidance)
            self.assertNotIn('High School Diploma',guidance)
        accountant=next(r for r in csv_rows('occupation_catalog.csv') if r['title']=='Accountants and Auditors')
        accountant['is_wfh_capable']=True
        self.assertIn('financial records',work_arrangement(accountant))

    def test_location_stays_local_and_requires_csrf(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('External geocoding is not used')):
            self.assertEqual(locate_province(14.3,120.96),'Cavite')
            result=self.client.post('/api/location',json={'latitude':14.3,'longitude':120.96})
        self.assertEqual(result.json['location'],'Cavite')
        self.assertEqual(self.client.post('/api/location',json={'latitude':0,'longitude':0}).status_code,422)
        self.assertEqual(self.client.post('/api/location',json={'latitude':True,'longitude':120}).status_code,400)
        self.assertEqual(self.client.post('/api/location',json={'latitude':14.3,'longitude':120.96},headers={'X-CSRF-Token':'wrong'}).status_code,403)
        self.assertIn('Cavite',self.client.get('/api/locations').json['locations'])
    def test_salary_provenance_returned_to_the_cards(self):
        result=self.client.post('/predict',json=self.profile).json
        for item in result['recommendations']:
            self.assertIn('salary_reference',item)
            ref=item['salary_reference']
            if ref['source_url']:
                self.assertTrue(ref['source_url'].startswith('https://'))
                self.assertIn(ref['match_type'],('exact','related'))
                self.assertIn(ref['year'],('2022','2026'))
    def test_salary_source_values_round_trip_and_legacy_columns_sync(self):
        rows=csv_rows('salary_ranges.csv')
        row=next(r for r in rows if r['occupation_title']=='Software Developers')
        source=json.loads((REFERENCE_DIR.parent/'source/ph_salary/jobstreet_ph_snapshot.json').read_text())
        original=next(r for r in source if r['source_url']==row['source_url'])
        self.assertEqual(float(row['min_amount']),original['p25']);self.assertEqual(float(row['max_amount']),original['p75'])
        self.assertEqual(float(row['median_amount']),original['median'])
        with database_connection(self.path) as db:
            stored=db.execute('SELECT * FROM salary_ranges WHERE onet_code=?',(row['onet_code'],)).fetchone()
            self.assertIn('middle 50%',stored['salary_display'])
            self.assertEqual(stored['source_occupation'],original['occupation'])
            self.assertEqual(db.execute('SELECT salary FROM occupations WHERE onet_code=?',(row['onet_code'],)).fetchone()[0],stored['salary_display'])
    def test_missing_salary_is_not_replaced_with_zero_or_generic_pay(self):
        with database_connection(self.path) as db:
            r=db.execute("SELECT * FROM salary_ranges WHERE data_status='unavailable' LIMIT 1").fetchone()
            self.assertIsNone(r['min_amount']);self.assertIsNone(r['max_amount'])
            self.assertIn('No matched',r['salary_display'])
            self.assertFalse(r['source_url'])
    def test_invalid_salary_import_rolls_back_other_changes(self):
        d=Path(self.tmp.name)/'invalid';d.mkdir()
        for n in ('college_programs','tesda_programs','salary_ranges'):(d/(n+'.csv')).write_bytes((REFERENCE_DIR/(n+'.csv')).read_bytes())
        file=d/'salary_ranges.csv'
        with file.open(newline='') as f:reader=csv.DictReader(f);cols=reader.fieldnames;rows=list(reader)
        row=next(r for r in rows if r['data_status']!='unavailable');row['median_amount']='999999999'
        with file.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
        with database_connection(self.path) as db:db.execute("UPDATE college_programs SET programs='KEEP THIS'")
        with self.assertRaises(ValueError):import_references(self.path,d)
        with database_connection(self.path) as db:self.assertEqual(db.execute('SELECT programs FROM college_programs LIMIT 1').fetchone()[0],'KEEP THIS')
    def test_salary_basis_distinguishes_industry_averages_and_advertised_ranges(self):
        rows=csv_rows('salary_ranges.csv')
        historical=next(r for r in rows if r['measure']=='industry_average_span')
        prepare_salary(historical);self.assertIn('industry averages',historical['salary_display']);self.assertIn('2022',historical['salary_display'])
        current=next(r for r in rows if r['measure']=='advertised_p25_p75')
        bad={**current,'min_amount':'nan'}
        with self.assertRaises(ValueError):prepare_salary(bad)
        bad={**current,'source_url':''}
        with self.assertRaises(ValueError):prepare_salary(bad)

if __name__=='__main__':unittest.main()
