"""Assessment history. Career saving is no longer part of the application."""
import json

def save_attempt(db, session_id, goal, education, scores, skills, responses):
    with db:
        db.execute("""INSERT INTO quiz_attempts
            (session_id, user_goal, education_level, riasec_scores, top_skills, question_responses)
            VALUES (?,?,?,?,?,?)""", (session_id, goal, education, json.dumps(scores),
            json.dumps(skills), json.dumps(responses)))

def occupation_title(db, code):
    row = db.execute('SELECT title FROM occupations WHERE onet_code=?', (code,)).fetchone()
    return row['title'] if row else None
