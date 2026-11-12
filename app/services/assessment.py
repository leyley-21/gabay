"""One authoritative 12-question definition and equal-weight RIASEC scoring."""
import json
import math
from functools import lru_cache
from app.config import REFERENCE_DIR

@lru_cache(maxsize=1)
def get_questions():
    questions = json.loads((REFERENCE_DIR / 'assessment_questions.json').read_text(encoding='utf-8'))
    if len(questions) != 12 or len({q['id'] for q in questions}) != 12:
        raise RuntimeError('The assessment must contain 12 unique questions.')
    if any(sum(q['trait'] == trait for q in questions) != 2 for trait in 'RIASEC'):
        raise RuntimeError('The assessment must have two items per RIASEC trait.')
    return questions

def score_responses(responses):
    questions = get_questions()
    if not isinstance(responses, dict) or set(responses) != {q['id'] for q in questions}:
        raise ValueError('Answer all 12 interest questions before continuing.')
    for value in responses.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 1 <= value <= 5:
            raise ValueError('Interest ratings must be numbers from 1 to 5.')
    return {trait: sum(responses[q['id']] for q in questions if q['trait'] == trait) / 2
            for trait in 'RIASEC'}
