"""HTTP endpoints: validate inputs, then delegate persistence and ranking."""
from flask import Blueprint, jsonify, render_template, request, session, send_file
import hashlib
import json
import re
from app.db import get_db
from app.services.feedback import FEEDBACK_TYPES, record_feedback
from app.recommendation.constants import EDU_ZONE_MAP, SKILL_KEYWORD_MAP
from app.recommendation.engine import recommend_career
from app.services.assessment import get_questions, score_responses

main = Blueprint('main', __name__)
GOALS = {'Immediate Workforce Entry', 'Work From Home / Home Caregiver',
         'Continue to College / Higher Ed', 'Vocational Certification (Tech-Voc)'}


def payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Send a JSON object.')
    return data


def required_text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > 250:
        raise ValueError(f'{key} must be a nonempty string (maximum 250 characters).')
    return value.strip()


@main.errorhandler(ValueError)
def invalid_input(error):
    return jsonify(status='error', message=str(error)), 400


@main.get('/')
def home():
    return render_template('index.html', assessment_questions=get_questions())


@main.post('/predict')
def predict():
    data = payload()
    session_id = session['anonymous_id']
    submission_id = required_text(data, 'submission_id')
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,100}', submission_id):
        raise ValueError('Invalid submission identifier.')
    goal = data.get('goal')
    education = data.get('education')
    if not isinstance(goal, str) or not isinstance(education, str) or goal not in GOALS or education not in EDU_ZONE_MAP:
        raise ValueError('Choose a valid goal and education level.')
    answers = data.get('answers')
    skills = data.get('skills', [])
    scores = score_responses(answers)
    if not isinstance(skills, list) or any(not isinstance(s, str) or s not in SKILL_KEYWORD_MAP for s in skills):
        raise ValueError('Choose skills from the supplied options.')
    db = get_db()
    canonical = json.dumps({'goal':goal,'education':education,'answers':answers,
                            'skills':sorted(set(skills))}, sort_keys=True, separators=(',',':'))
    request_hash = hashlib.sha256(canonical.encode()).hexdigest()
    # The transaction makes concurrent retries atomic across server workers.
    with db:
        db.execute('BEGIN IMMEDIATE')
        prior = db.execute('SELECT request_hash,response_json FROM assessment_submissions WHERE session_id=? AND submission_id=?',
                           (session_id,submission_id)).fetchone()
        if prior:
            if prior['request_hash'] != request_hash:
                return jsonify(status='error',message='This submission ID belongs to different answers.'),409
            return jsonify(json.loads(prior['response_json']))
        recommendations = recommend_career(goal, education, scores, skills, db)
        result = dict(status='success', recommendations=recommendations, riasec_scores=scores,
                      assessment_context={'goal':goal,'education':education})
        # Avoid a nested transaction: store history and the response in one commit.
        db.execute("""INSERT INTO quiz_attempts
            (session_id,user_goal,education_level,riasec_scores,top_skills,question_responses)
            VALUES (?,?,?,?,?,?)""",(session_id,goal,education,json.dumps(scores),json.dumps(skills),json.dumps(answers)))
        db.execute('INSERT INTO assessment_submissions(session_id,submission_id,request_hash,response_json) VALUES (?,?,?,?)',
                   (session_id,submission_id,request_hash,json.dumps(result)))
    return jsonify(result)



@main.post('/log_implicit_feedback')
def log_feedback():
    data = payload()
    data['session_id'] = session['anonymous_id']
    data['onet_code'] = required_text(data, 'onet_code')
    action = data.get('feedback_type')
    if not isinstance(action, str) or action not in FEEDBACK_TYPES:
        raise ValueError('Unsupported feedback type.')
    db = get_db()
    submission_id = required_text(data, 'submission_id')
    submitted = db.execute('SELECT response_json FROM assessment_submissions WHERE session_id=? AND submission_id=?',
                           (data['session_id'],submission_id)).fetchone()
    if submitted is None:
        raise ValueError('Complete your assessment before giving feedback.')
    result = json.loads(submitted['response_json'])
    # Bind feedback to the exact assessment that generated these recommendations.
    scores = result['riasec_scores']
    # Use fixed RIASEC tie ordering, identical to the ranker.
    traits = sorted('RIASEC', key=lambda trait: scores[trait], reverse=True)
    data['riasec_cluster'] = '-'.join(traits[:2])
    context = result.get('assessment_context', {})
    data['goal'] = context.get('goal')
    data['education'] = context.get('education')
    if data['onet_code'] == 'APP_RETAKE':
        if action != 'quick_retake_mismatch':
            raise ValueError('Invalid retake feedback.')
    elif data['onet_code'] not in {item['code'] for item in result['recommendations']}:
        raise ValueError('Give feedback only on careers recommended in this assessment.')
    record_feedback(db, data)
    return jsonify(status='logged')


@main.get('/health')
def health():
    db = get_db()
    if not db.execute('SELECT COUNT(*) FROM occupations').fetchone()[0]:
        return jsonify(status='unavailable'), 503
    return jsonify(status='ok')


@main.get('/api/locations')
def location_choices():
    from app.services.location import province_names
    return jsonify(locations=province_names())


@main.post('/api/location')
def resolve_location():
    from app.services.location import locate_province
    data=payload()
    province=locate_province(data.get('latitude'),data.get('longitude'))
    if not province:
        return jsonify(status='not_found',message='We could not identify your province. Please enter your city or province.'),422
    return jsonify(status='success',location=province,
        note='Approximate province from a 2020 boundary snapshot. Please check or change it.')



@main.post('/api/career-report')
def career_report():
    data = payload()
    submission_id = required_text(data, 'submission_id')
    row = get_db().execute(
        'SELECT response_json FROM assessment_submissions WHERE session_id=? AND submission_id=?',
        (session['anonymous_id'], submission_id)).fetchone()
    if row is None:
        return jsonify(status='error', message='Complete your assessment before downloading its career cards.'), 404
    result = json.loads(row['response_json'])
    if not result.get('recommendations'):
        return jsonify(status='error', message='There are no career cards to download.'), 400
    from app.services.career_pdf import build_career_pdf
    return send_file(build_career_pdf(result), mimetype='application/pdf', as_attachment=True,
                     download_name='ALS-Gabay-Career-Cards.pdf', max_age=0)
