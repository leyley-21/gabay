"""Session-bound, complete and read-only PDF exports."""
import json, unittest
from io import BytesIO
from pypdf import PdfReader
import test_application as fixtures
from app.db import database_connection
from app.services.career_pdf import build_career_pdf

class CareerPDFTests(unittest.TestCase):
    setUp = fixtures.ApplicationTests.setUp
    tearDown = fixtures.ApplicationTests.tearDown

    def assessment(self):
        data = {**self.profile, 'submission_id':'pdf_export_submission_123'}
        result = self.client.post('/predict', json=data)
        self.assertEqual(result.status_code,200)
        return data['submission_id'], result.json

    def test_export_contains_all_pages_and_expanded_sections_without_new_attempt(self):
        submission_id, result = self.assessment()
        response = self.client.post('/api/career-report', json={'submission_id':submission_id})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.mimetype,'application/pdf')
        self.assertIn('attachment;',response.headers['Content-Disposition'])
        self.assertIn('no-store',response.headers['Cache-Control'])
        reader = PdfReader(BytesIO(response.data))
        text = '\n'.join(p.extract_text() for p in reader.pages)
        self.assertGreaterEqual(len(reader.pages),len(result['recommendations']))
        for item in result['recommendations']:
            self.assertIn(item['title'],text)
        self.assertIn('Why This May Suit You',text)
        self.assertIn('Career Details & Next Steps',text)
        self.assertTrue(any(p.get('/Annots') for p in reader.pages))
        with database_connection(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM quiz_attempts').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM raw_feedback_logs').fetchone()[0],0)

    def test_another_session_cannot_export_the_submission(self):
        submission_id,_ = self.assessment()
        other = self.app.test_client();other.get('/')
        with other.session_transaction() as s:token=s['csrf_token']
        r=other.post('/api/career-report',json={'submission_id':submission_id},headers={'X-CSRF-Token':token})
        self.assertEqual(r.status_code,404)

    def test_export_requires_session_and_csrf(self):
        fresh = self.app.test_client()
        self.assertEqual(fresh.post('/api/career-report',json={'submission_id':'unknown'}).status_code,403)
        self.client.environ_base.pop('HTTP_X_CSRF_TOKEN')
        self.assertEqual(self.client.post('/api/career-report',json={'submission_id':'unknown'}).status_code,403)

    def test_missing_submission_is_not_exported(self):
        self.assertEqual(self.client.post('/api/career-report',json={'submission_id':'unknown'}).status_code,404)

    def test_long_cards_wrap_without_losing_content_or_parsing_source_markup(self):
        result={'recommendations':[{'title':'Long career & work <test>',
            'college_majors':'Long Program Name | '*250,
            'description':'Work safely & check <equipment>. '*200+'END_OF_LONG_CAREER',
            'fit_reasons':['A detailed reason. '*80+'END_OF_FIT_REASON']}], 'assessment_context':{'goal':'Continue to College / Higher Ed'}}
        reader=PdfReader(build_career_pdf(result));text='\n'.join(p.extract_text() for p in reader.pages)
        self.assertGreater(len(reader.pages),1)
        self.assertIn('END_OF_LONG_CAREER',text)
        self.assertIn('END_OF_FIT_REASON',text)
        self.assertIn('Work safely & check <equipment>.',text)
