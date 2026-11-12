import uuid
import unittest
from concurrent.futures import ThreadPoolExecutor
import test_application as fixtures
from app.db import database_connection
from app.services.feedback import record_feedback,rebuild_summary

class ProtectionTests(unittest.TestCase):
    setUp=fixtures.ApplicationTests.setUp
    tearDown=fixtures.ApplicationTests.tearDown
    def submit(self,**overrides):
        return self.client.post('/predict',json={**self.profile,**overrides})
    def test_session_and_csrf(self):
        outsider=self.app.test_client()
        self.assertEqual(outsider.post('/predict',json=self.profile).status_code,403)
        page=outsider.get('/')
        self.assertIn('HttpOnly',page.headers['Set-Cookie'])
        self.assertIn('SameSite=Lax',page.headers['Set-Cookie'])
        self.assertEqual(page.headers['Cache-Control'],'no-store')
        self.assertEqual(outsider.post('/predict',json=self.profile).status_code,403)
        outsider.set_cookie('session',outsider.get_cookie('session').value+'tampered')
        self.assertEqual(outsider.post('/predict',json=self.profile,headers={'X-CSRF-Token':'forged'}).status_code,403)
        self.assertEqual(self.submit(session_id='forged').status_code,200)
        with self.client.session_transaction() as s: identity=s['anonymous_id']
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT session_id FROM quiz_attempts').fetchone()[0],identity)
    def test_retry_and_conflict(self):
        key=uuid.uuid4().hex
        first=self.submit(submission_id=key)
        self.assertEqual(first.json,self.submit(submission_id=key).json)
        self.assertEqual(self.submit(submission_id=key,answers={**self.profile['answers'],'R1':5}).status_code,409)
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM quiz_attempts').fetchone()[0],1)
    def test_concurrent_retries(self):
        key=uuid.uuid4().hex;cookie=self.client.get_cookie('session').value
        csrf=self.client.environ_base['HTTP_X_CSRF_TOKEN']
        def send(_):
            client=self.app.test_client();client.set_cookie('session',cookie)
            return client.post('/predict',json={**self.profile,'submission_id':key},headers={'X-CSRF-Token':csrf})
        with ThreadPoolExecutor(max_workers=2) as pool: responses=list(pool.map(send,range(2)))
        self.assertEqual([r.status_code for r in responses],[200,200])
        self.assertEqual(responses[0].json,responses[1].json)
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM quiz_attempts').fetchone()[0],1)
    def test_feedback_identity_and_profile_binding(self):
        key=uuid.uuid4().hex;result=self.submit(submission_id=key).json
        job=result['recommendations'][0]['code']
        data=dict(submission_id=key,onet_code=job,feedback_type='helpful',session_id='fake',goal='fake',education='fake',riasec_cluster='fake')
        for identity in ['fake','another']:
            self.assertEqual(self.client.post('/log_implicit_feedback',json={**data,'session_id':identity}).status_code,200)
        with database_connection(self.path) as db:
            rows=db.execute('SELECT * FROM raw_feedback_logs').fetchall();self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['user_goal'],self.profile['goal']);self.assertEqual(rows[0]['riasec_cluster'],'R-I')
            shown={j['code'] for j in result['recommendations']}
            unshown=next(r[0] for r in db.execute('SELECT onet_code FROM occupations') if r[0] not in shown)
        self.assertEqual(self.client.post('/log_implicit_feedback',json={**data,'onet_code':unshown}).status_code,400)
        self.assertEqual(self.client.post('/log_implicit_feedback',json={**data,'submission_id':'missing'}).status_code,400)
    def test_rate_limits(self):
        self.app.config['RATE_LIMITS']['predict_session']=(1,60)
        self.assertEqual(self.submit().status_code,200)
        response=self.submit();self.assertEqual(response.status_code,429)
        self.assertGreater(int(response.headers['Retry-After']),0)
        self.app.config['RATE_LIMITS']['session_issue']=(1,600)
        self.assertEqual(self.app.test_client().get('/').status_code,429)
    def test_incremental_feedback_matches_full_rebuild(self):
        data=dict(session_id='voter',onet_code=self.code,goal='old',education='Junior High School',riasec_cluster='R-I',feedback_type='helpful')
        with database_connection(self.path) as db:
            db.execute('INSERT INTO job_feedback_summary(onet_code,riasec_cluster,user_goal,net_score_boost,total_interactions) VALUES (?,?,?,99,99)',(self.code,'S-E','untouched'));db.commit()
            record_feedback(db,data)
            record_feedback(db,{**data,'goal':'new','riasec_cluster':'A-S','feedback_type':'not_relevant'})
            self.assertEqual(db.execute("SELECT COUNT(*) FROM job_feedback_summary WHERE user_goal='old'").fetchone()[0],0)
            self.assertEqual(db.execute("SELECT net_score_boost FROM job_feedback_summary WHERE user_goal='new'").fetchone()[0],-1)
            self.assertEqual(db.execute("SELECT net_score_boost FROM job_feedback_summary WHERE user_goal='untouched'").fetchone()[0],99)
            db.execute("DELETE FROM job_feedback_summary WHERE user_goal='untouched'");db.commit()
            query='SELECT onet_code,riasec_cluster,user_goal,total_interactions,net_score_boost FROM job_feedback_summary ORDER BY 1,2,3'
            before=[tuple(r) for r in db.execute(query)];rebuild_summary(db)
            self.assertEqual(before,[tuple(r) for r in db.execute(query)])
