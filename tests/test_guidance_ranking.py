"""Behavior checks for genuine skill evidence and future-study guidance."""
import unittest
from app.db import database_connection
from app.recommendation.constants import SKILL_KEYWORD_MAP
from app.recommendation.explanations import matching_skills
from app.recommendation.engine import recommend_career
import test_application as fixtures

class GuidanceRankingTests(unittest.TestCase):
    setUp=fixtures.ApplicationTests.setUp
    tearDown=fixtures.ApplicationTests.tearDown

    def test_generic_words_do_not_create_unrelated_skill_matches(self):
        row={'title':'Office Assistants','description':'Support the office team, enter data, and contact a representative.'}
        skills=['Programming and coding','Caregiving support','Community health assistance','Selling products','Computers and hardware']
        self.assertEqual(matching_skills(row,skills,SKILL_KEYWORD_MAP),[])
        row={'title':'Electrical Engineers','description':'Design electrical equipment.'}
        self.assertEqual(matching_skills(row,['Repairs and maintenance'],SKILL_KEYWORD_MAP),[])

    def test_specific_career_duties_and_plural_titles_match(self):
        row={'title':'Software Developers','description':'Research, design, and develop computer and network software.'}
        self.assertEqual(matching_skills(row,['Programming and coding','Caregiving support'],SKILL_KEYWORD_MAP),['Programming and coding'])
        row={'title':'Personal Care Aides','description':'Help older adults with daily activities.'}
        self.assertEqual(matching_skills(row,['Caregiving support','Childcare & Elderly support'],SKILL_KEYWORD_MAP),['Caregiving support','Childcare & Elderly support'])

    def test_college_exploration_is_not_penalized_for_current_education(self):
        scores=dict.fromkeys('RIASEC',3)
        with database_connection(self.path) as db:
            elementary=recommend_career('Continue to College / Higher Ed','Elementary Level',scores,[],db,use_feedback=False)
            senior=recommend_career('Continue to College / Higher Ed','Senior High School',scores,[],db,use_feedback=False)
        self.assertEqual([j['code'] for j in elementary],[j['code'] for j in senior])
        self.assertTrue(all(j['ranking_factors']['preparation_adjustment']==0 for j in elementary))

    def test_vocational_suggestions_have_a_mapped_qualification(self):
        with database_connection(self.path) as db:
            jobs=recommend_career('Technical-Vocational / TESDA','Junior High School',dict.fromkeys('RIASEC',3),[],db,use_feedback=False)
        self.assertEqual(len(jobs),30)
        self.assertTrue(all(job['tesda_options'] for job in jobs))
        self.assertTrue(all(job['preparation_note'] for job in jobs if job['job_zone']>=4))

    def test_salary_cannot_change_recommendation_order(self):
        scores=dict.fromkeys('RIASEC',3)
        with database_connection(self.path) as db:
            before=recommend_career('Continue to College / Higher Ed','Junior High School',scores,[],db,use_feedback=False)
            db.execute("UPDATE salary_ranges SET salary_display='PHP 999,999 / month'")
            after=recommend_career('Continue to College / Higher Ed','Junior High School',scores,[],db,use_feedback=False)
        self.assertEqual([j['code'] for j in before],[j['code'] for j in after])

if __name__=='__main__':unittest.main()
