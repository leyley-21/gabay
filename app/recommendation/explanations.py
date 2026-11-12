"""Deterministic explanations grounded in each occupation's stored O*NET evidence."""
import re
from functools import lru_cache
from app.config import RIASEC_COLUMNS

@lru_cache(maxsize=64)
def _skill_pattern(keywords):
    return re.compile(r'\b(?:'+'|'.join(re.escape(word) for word in keywords)+r')(?:s|es)?\b',re.IGNORECASE)

def matching_skills(row,skills,keyword_map):
    text=(row['title']+' '+row['description'])
    return [skill for skill in skills if keyword_map.get(skill) and _skill_pattern(tuple(keyword_map[skill])).search(text)]


def build_fit_reasons(row, scores, skills, goal, education, allowed_zones, matched_skills):
    features = dict(zip('RIASEC', (float(row[c]) for c in RIASEC_COLUMNS)))
    strongest = sorted(features, key=features.get, reverse=True)[:2]
    shared = sorted('RIASEC', key=lambda t: ((scores[t]-1)/4) * ((features[t]-1)/6), reverse=True)[:2]
    activities = {'R':'making, fixing, or working with tools','I':'finding answers and solving problems',
        'A':'creating and expressing ideas','S':'helping and supporting people',
        'E':'leading, selling, or sharing ideas','C':'organizing information and checking details'}
    reasons = [f"{row['title']} often involves {activities[strongest[0]]}."]
    if max(scores.values()) <= 3:
        reasons.append('Your answers do not show a strong preference yet. Treat this as a career idea to explore.')
    else:
        trait=shared[0]
        if scores[trait] >= 3.5:
            reasons.append(f"Your answers show interest in {activities[trait]}. That interest is one reason this career is suggested.")
        else:
            reasons.append('This option is less aligned with your strongest interests, but your other preferences brought it into the results.')
    description=' '.join(row['description'].split())
    if description:
        excerpt=description[:220].rsplit(' ',1)[0]+'…' if len(description)>220 else description
        reasons.append('Work you may do: '+excerpt)
    if matched_skills:
        reasons.append('Skills you selected that may relate to this work: '+', '.join(matched_skills)+'. You can build on these through practice or training.')
    if row['job_zone'] not in allowed_zones:
        reasons.append('This career may need more study, training, or experience. Check the actual local requirements before planning your next step.')
    else:
        reasons.append('Check what qualifications local employers or schools require. Your education level alone does not confirm eligibility.')
    if 'Work From Home' in goal:
        reasons.append('Some roles in this field may allow remote work. Check each job listing.' if row['is_wfh_capable'] else 'This work may need an on-site workplace, which may not suit your work-from-home goal.')
    return reasons


def build_fit_evidence(row, scores=None, matched_skills=None):
    """Return stored O*NET occupation-description sentences without authored fit text.

    The optional arguments preserve the existing API signature. Interest/skill
    inputs affect career ranking, not the wording of the source description.
    """
    description = (row['description'] or '').strip()
    sentences = list(dict.fromkeys(filter(None, re.split(r'(?<=[.!?])\s+', description))))
    return [dict(task=sentence, explanation='', heading='', connections=[],
                 source='O*NET occupation description') for sentence in sentences]


def build_fit_cautions(row, scores, goal):
    return []


