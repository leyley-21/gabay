"""Isolated integration checks. Never modify the included database."""
import csv,json,tempfile,unittest,uuid
from flask.testing import FlaskClient
from pathlib import Path
from app import create_app
from app.config import REFERENCE_DIR
from app.db import database_connection
from app.schema import initialize_database
from app.services.assessment import get_questions,score_responses
from app.services.catalog import import_catalog,import_references
from app.services.feedback import rebuild_summary

class AnonymousClient(FlaskClient):
    def post(self, url, *args, **kwargs):
        if url == '/predict' and isinstance(kwargs.get('json'),dict):
            kwargs['json'] = dict(kwargs['json'])
            kwargs['json'].setdefault('submission_id', uuid.uuid4().hex)
        return super().post(url, *args, **kwargs)

class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'test.db'
        initialize_database(self.path);import_catalog(self.path);import_references(self.path)
        self.app=create_app({'TESTING':True,'DATABASE':str(self.path)});self.app.test_client_class=AnonymousClient;self.client=self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as session:
            self.client.environ_base['HTTP_X_CSRF_TOKEN']=session['csrf_token']
        self.profile=dict(session_id='test',goal='Immediate Workforce Entry',education='Junior High School',answers={q['id']:3 for q in get_questions()},skills=[])
        with database_connection(self.path) as db:self.code=db.execute('SELECT onet_code FROM occupations LIMIT 1').fetchone()[0]
    def tearDown(self):self.tmp.cleanup()
    def test_frontend_education_choices_are_accepted(self):
        import re
        source = (Path(__file__).resolve().parents[1] / 'app/static/js/assessment-options.js').read_text()
        levels = re.findall(r'level: "([^"]+)"', source)
        self.assertEqual(len(levels), 4)
        for level in levels:
            with self.subTest(education=level):
                response = self.client.post('/predict', json={**self.profile, 'education': level})
                self.assertEqual(response.status_code, 200, response.data)

    def test_two_answers_per_trait(self):
        answers={q['id']:1 for q in get_questions()}
        for t in 'RIASEC':answers[t+'2']=5
        self.assertEqual(score_responses(answers),dict.fromkeys('RIASEC',3))
        answers['R2']=3;self.assertEqual(score_responses(answers)['R'],2)
    def test_prediction_explanations_and_response_history(self):
        response=self.client.post('/predict',json=self.profile);self.assertEqual(response.status_code,200,response.data)
        jobs=response.json['recommendations'];self.assertEqual(len(jobs),30)
        self.assertEqual(len({tuple(j['fit_reasons']) for j in jobs}),30)
        with database_connection(self.path) as db:row=db.execute('SELECT riasec_scores,question_responses FROM quiz_attempts').fetchone()
        self.assertEqual(len(json.loads(row['question_responses'])),12)
        self.assertEqual(json.loads(row['riasec_scores']),dict.fromkeys('RIASEC',3))
    def test_reject_incomplete_and_invalid_answers(self):
        for a in [dict.fromkeys('RIASEC',3),{},None,{**self.profile['answers'],'R2':6},{**self.profile['answers'],'C1':True}]:
            self.assertEqual(self.client.post('/predict',json={**self.profile,'answers':a}).status_code,400)
    def test_new_questions_change_ranking(self):
        a={q['id']:1 for q in get_questions()};b=dict(a)
        a.update(R1=5,R2=5);b.update(A1=5,A2=5)
        j1=self.client.post('/predict',json={**self.profile,'answers':a}).json['recommendations']
        j2=self.client.post('/predict',json={**self.profile,'answers':b}).json['recommendations']
        self.assertNotEqual([j['code'] for j in j1[:5]],[j['code'] for j in j2[:5]])
    def test_references_read_from_db(self):
        with database_connection(self.path) as db:
            db.execute("UPDATE college_programs SET programs='TEST COLLEGE'");db.execute("UPDATE tesda_programs SET qualifications='TEST TESDA'");db.execute("UPDATE salary_ranges SET salary_display='TEST SALARY'")
        j=self.client.post('/predict',json=self.profile).json['recommendations'][0]
        self.assertEqual((j['college_majors'],j['tech_voc'],j['salary']),('TEST COLLEGE','TEST TESDA','TEST SALARY'))
    def test_csv_import_is_atomic(self):
        d=Path(self.tmp.name)/'csv';d.mkdir()
        for n in ['college_programs','tesda_programs','salary_ranges']:(d/(n+'.csv')).write_bytes((REFERENCE_DIR/(n+'.csv')).read_bytes())
        file=d/'college_programs.csv'
        with file.open(newline='') as f:r=csv.DictReader(f);cols=r.fieldnames;rows=list(r)
        rows[0]['programs']='Imported course'
        with file.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
        import_references(self.path,d)
        with database_connection(self.path) as db:self.assertEqual(db.execute('SELECT programs FROM college_programs WHERE onet_code=?',(rows[0]['onet_code'],)).fetchone()[0],'Imported course')
        (d/'salary_ranges.csv').write_text('onet_code\nmissing\n')
        with self.assertRaises((ValueError,KeyError)):import_references(self.path,d)
        with database_connection(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM salary_ranges').fetchone()[0],923)
    def test_feedback_replacement_and_stale_cleanup(self):
        self.profile['submission_id']=uuid.uuid4().hex
        self.code=self.client.post('/predict',json=self.profile).json['recommendations'][0]['code']
        d=dict(session_id='test',submission_id=self.profile['submission_id'],onet_code=self.code,goal=self.profile['goal'],education=self.profile['education'],riasec_cluster='R-I',feedback_type='helpful')
        for _ in range(2):self.assertEqual(self.client.post('/log_implicit_feedback',json=d).status_code,200)
        self.client.post('/log_implicit_feedback',json={**d,'feedback_type':'not_relevant'})
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM raw_feedback_logs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT net_score_boost FROM job_feedback_summary').fetchone()[0],-1)
            db.execute('DELETE FROM raw_feedback_logs');rebuild_summary(db)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM job_feedback_summary').fetchone()[0],0)
    def test_saving_removed(self):
        self.assertEqual(self.client.post('/api/save-career',json={}).status_code,404)
        self.assertEqual(self.client.get('/api/saved-careers/test').status_code,404)
        self.assertNotIn(b'nav-saved',self.client.get('/').data)
        with database_connection(self.path) as db:self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='saved_careers'").fetchone())
    def test_initialize_preserves_history(self):
        self.client.post('/predict',json=self.profile);initialize_database(self.path);import_catalog(self.path);import_references(self.path)
        with database_connection(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM quiz_attempts').fetchone()[0],1)
    def test_health_and_assets(self):
        self.assertEqual(self.client.get('/health').json['status'],'ok')
        for n in ['api-client','assessment-options','assessment','career-results','page-navigation']:
            with self.client.get('/static/js/'+n+'.js') as response:self.assertEqual(response.status_code,200)


class RankingRegressionTests(unittest.TestCase):
    setUp = ApplicationTests.setUp
    tearDown = ApplicationTests.tearDown

    def test_cache_reused_across_history_writes_and_invalidated_on_catalog_edit(self):
        from app.recommendation.engine import _prepare_catalog
        _prepare_catalog.cache_clear()
        self.client.post('/predict',json=self.profile)
        first=_prepare_catalog.cache_info()
        self.client.post('/predict',json=self.profile)
        second=_prepare_catalog.cache_info()
        self.assertEqual(first.misses,1)
        self.assertEqual(second.hits,1)
        with database_connection(self.path) as db:db.execute("UPDATE college_programs SET programs='Updated after cache warmup'")
        job=self.client.post('/predict',json=self.profile).json['recommendations'][0]
        self.assertEqual(job['college_majors'],'Updated after cache warmup')
        self.assertEqual(_prepare_catalog.cache_info().misses,2)

    def test_full_catalog_reranking_includes_contextual_match_outside_first_150(self):
        with database_connection(self.path) as db:
            code=db.execute('SELECT onet_code FROM occupations ORDER BY onet_code DESC LIMIT 1').fetchone()[0]
            db.execute('UPDATE occupations SET realistic=4,investigative=4,artistic=4,social=4,enterprising=4,conventional=4,is_wfh_capable=0,job_zone=2')
            db.execute('UPDATE occupations SET realistic=4.6,investigative=4.6,artistic=4.6,social=4.6,enterprising=4.6,conventional=4.6,is_wfh_capable=1 WHERE onet_code=?',(code,))
        profile={**self.profile,'goal':'Work From Home / Home Caregiver'}
        jobs=self.client.post('/predict',json=profile).json['recommendations']
        self.assertEqual(jobs[0]['code'],code)

    def test_numeric_proximity_matches_independent_euclidean_calculation(self):
        import math
        from app.config import RIASEC_COLUMNS
        from app.recommendation.engine import recommend_career
        scores=dict(zip('RIASEC',[4.5,2,3.5,1.5,4,2.5]))
        with database_connection(self.path) as db:
            jobs=recommend_career(self.profile['goal'],self.profile['education'],scores,[],db)
            for job in jobs:
                row=db.execute('SELECT * FROM occupations WHERE onet_code=?',(job['code'],)).fetchone()
                distance=math.sqrt(sum(((scores[t]-1)/4-(row[c]-1)/6)**2 for t,c in zip('RIASEC',RIASEC_COLUMNS)))
                expected=round(max(0,1-distance/math.sqrt(6))*100,2)
                self.assertAlmostEqual(job['base_match'],expected,places=2)

    def test_new_feedback_is_read_without_refitting_the_catalog(self):
        from app.recommendation.engine import _prepare_catalog
        _prepare_catalog.cache_clear()
        first=self.client.post('/predict',json=self.profile).json['recommendations']
        target=first[-1]
        misses=_prepare_catalog.cache_info().misses
        with database_connection(self.path) as db:
            db.execute("INSERT INTO job_feedback_summary(onet_code,riasec_cluster,user_goal,total_interactions,net_score_boost) VALUES (?,?,?,?,?)",(target['code'],'R-I',self.profile['goal'],2,2.0))
        second=self.client.post('/predict',json=self.profile).json['recommendations']
        updated=next(job for job in second if job['code']==target['code'])
        self.assertEqual(updated['match_score'],round(min(98.5,target['match_score']+3),1))
        self.assertEqual(_prepare_catalog.cache_info().misses,misses)

if __name__=='__main__':unittest.main()
