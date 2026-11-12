"""Cached nearest-neighbor matching with vectorized, full-catalog reranking."""
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from threading import Lock
import math
import numpy as np
from sklearn.neighbors import NearestNeighbors
from app.config import RIASEC_COLUMNS
from app.db import database_connection
from app.services.programs import program_options
from app.services.work_arrangements import work_arrangement
from app.recommendation.constants import EDU_ZONE_MAP, SKILL_KEYWORD_MAP
from app.recommendation.explanations import build_fit_reasons, build_fit_evidence, build_fit_cautions, matching_skills

CATALOG_QUERY = """SELECT o.*,
    c.programs AS college_programs, c.data_status AS college_status,
    t.qualifications AS tesda_qualifications, t.data_status AS tesda_status,
    s.salary_display AS salary_display, s.data_status AS salary_status,
    s.source_url AS salary_source_url, s.source_occupation AS salary_source_occupation,
    s.source_name AS salary_source_name, s.reference_year AS salary_reference_year,
    s.measure AS salary_measure, s.match_type AS salary_match_type, s.mapping_note AS salary_mapping_note,
    s.median_amount AS salary_median, s.reviewed_on AS salary_reviewed_on
    FROM occupations o LEFT JOIN college_programs c USING(onet_code)
    LEFT JOIN tesda_programs t USING(onet_code) LEFT JOIN salary_ranges s USING(onet_code)
    ORDER BY o.onet_code"""

@dataclass(frozen=True)
class RankingWeights:
    interest: float = 0.8
    education_penalty: float = 15.0
    skill_per_match: float = 4.0
    skill_cap: float = 12.0
    goal_multiplier: float = 1.0
    feedback_multiplier: float = 1.0

    def __post_init__(self):
        if any(not isinstance(value,(int,float)) or isinstance(value,bool) or
               not math.isfinite(value) or value < 0 for value in self.__dict__.values()):
            raise ValueError('Ranking weights must be finite nonnegative numbers.')

DEFAULT_WEIGHTS = RankingWeights()

@dataclass(frozen=True)
class CatalogIndex:
    rows: tuple
    model: NearestNeighbors
    zones: np.ndarray
    remote: np.ndarray
    skill_matches: dict
    lock: object

@lru_cache(maxsize=4)
def _prepare_catalog(columns, records):
    # Cache by the actual imported contents, not file mtime. Quiz/feedback writes
    # do not invalidate this cache; committed catalog/reference edits do.
    rows = tuple(MappingProxyType(dict(zip(columns, row))) for row in records)
    features = np.asarray([[float(row[c]) for c in RIASEC_COLUMNS] for row in rows],dtype=float)
    if not np.isfinite(features).all() or np.any((features<1)|(features>7)):
        raise ValueError('Career interest data must contain six finite ratings from 1 to 7.')
    model = NearestNeighbors(metric='euclidean',algorithm='kd_tree',n_jobs=1).fit((features-1)/6)
    zones = np.asarray([int(row['job_zone']) for row in rows])
    remote = np.asarray([bool(row['is_wfh_capable']) for row in rows])
    for array in (zones,remote): array.setflags(write=False)
    return CatalogIndex(rows,model,zones,remote,{},Lock())

def _skill_flags(catalog,skill):
    # Prepare only the skills this user selected. Each skill is scanned once per
    # catalog version, including when multiple Waitress threads request it.
    with catalog.lock:
        if skill not in catalog.skill_matches:
            flags=np.fromiter((bool(matching_skills(row,(skill,),SKILL_KEYWORD_MAP)) for row in catalog.rows),dtype=bool,count=len(catalog.rows))
            flags.setflags(write=False)
            catalog.skill_matches[skill]=flags
        return catalog.skill_matches[skill]

def _load_catalog(db):
    cursor = db.execute(CATALOG_QUERY)
    columns = tuple(column[0] for column in cursor.description)
    records = tuple(tuple(row) for row in cursor.fetchall())
    if not records:
        raise RuntimeError('Career list is empty. Run python manage.py initialize-database.')
    return _prepare_catalog(columns,records)

def recommend_career(goal,education,scores,skills,db=None,weights=DEFAULT_WEIGHTS, use_feedback=True):
    if db is None:
        with database_connection() as connection:
            return recommend_career(goal,education,scores,skills,connection,weights,use_feedback)
    catalog = _load_catalog(db)
    vector = np.asarray([[(scores[trait]-1)/4 for trait in 'RIASEC']],dtype=float)
    # Consider every occupation before applying goal, education, skill and
    # feedback adjustments. A valid contextual match cannot be dropped at 150.
    distances,indices = catalog.model.kneighbors(vector,n_neighbors=len(catalog.rows))
    distance = np.empty(len(catalog.rows),dtype=float)
    distance[indices[0]] = distances[0]
    proximity = np.clip(1-distance/math.sqrt(6),0,1)*100
    allowed_zones = EDU_ZONE_MAP[education]
    # College is a future study goal, not an application for a job today.
    # Do not downrank an aspirational degree career for the learner's current stage.
    education_penalty = (np.zeros(len(catalog.rows)) if 'College' in goal else
                         np.where(np.isin(catalog.zones,allowed_zones),0.0,weights.education_penalty))
    has_tesda = np.asarray([bool((row['tesda_qualifications'] or '').strip()) for row in catalog.rows])
    eligible = np.ones(len(catalog.rows), dtype=bool)
    goal_boost = np.zeros(len(catalog.rows))
    if 'Vocational' in goal:
        # A vocational recommendation needs an actual mapped training option.
        eligible = has_tesda
        goal_boost = np.where(has_tesda & (catalog.zones<=3),6.0,0.0)
    elif 'Work From Home' in goal: goal_boost = np.where(catalog.remote,12.0,-25.0)
    elif 'Immediate Workforce' in goal: goal_boost = np.where(catalog.zones<=2,5.0,0.0)
    elif 'College' in goal: goal_boost = np.where(catalog.zones>=3,5.0,0.0)
    selected = tuple(dict.fromkeys(skills))
    skill_flags={skill:_skill_flags(catalog,skill) for skill in selected}
    skill_counts = np.sum(tuple(skill_flags.values()),axis=0) if selected else np.zeros(len(catalog.rows))
    skill_boost = np.minimum(skill_counts*weights.skill_per_match,weights.skill_cap)
    traits = sorted(scores,key=scores.get,reverse=True)
    cluster = '-'.join(traits[:2])
    # Never cache feedback: another user's new vote is available on the next request.
    boosts = dict(db.execute('SELECT onet_code,net_score_boost FROM job_feedback_summary WHERE user_goal=? AND riasec_cluster=?',(goal,cluster)).fetchall()) if use_feedback else {}
    community = np.asarray([max(-10,min(10,boosts.get(row['onet_code'],0)*1.5)) for row in catalog.rows])
    composite = proximity*weights.interest+goal_boost*weights.goal_multiplier+skill_boost-education_penalty+community*weights.feedback_multiplier
    # Rank on full precision. Rounding/display caps must not create artificial ties.
    order = sorted(np.flatnonzero(eligible),key=lambda i:(-float(composite[i]),-float(proximity[i]),catalog.rows[i]['onet_code']))[:30]
    candidates=[]
    for idx in order:
        row=catalog.rows[idx]
        matched=[skill for skill in selected if skill_flags[skill][idx]]
        statuses={row['college_status'],row['tesda_status'],row['salary_status']}
        note=('Course ideas and pay estimates need local confirmation.' if 'legacy_estimate' in statuses
              else 'Check current course requirements, availability, and local pay.')
        candidates.append(dict(title=row['title'],code=row['onet_code'],
            match_score=round(float(np.clip(composite[idx],0,98.5)),1),base_match=round(float(proximity[idx]),2),
            description=row['description'],job_zone=int(row['job_zone']),
            preparation_note=('The TESDA options build related skills. This full career may also require a degree, professional registration, or additional experience.'
                              if 'Vocational' in goal and int(row['job_zone']) >= 4 else ''),
            ranking_factors=dict(interest_component=round(float(proximity[idx]*weights.interest),4),
                skill_component=round(float(skill_boost[idx]),4),
                matched_skills=matched,goal_component=round(float(goal_boost[idx]*weights.goal_multiplier),4),
                preparation_adjustment=-round(float(education_penalty[idx]),4),
                feedback_component=round(float(community[idx]*weights.feedback_multiplier),4)),
            college_majors=row['college_programs'] or '',tech_voc=row['tesda_qualifications'] or '',
            college_options=program_options(row['college_programs'], 'college'),
            tesda_options=program_options(row['tesda_qualifications'], 'tesda'),
            salary=row['salary_display'] or '',
            salary_reference=dict(source_url=row['salary_source_url'] or '',source_occupation=row['salary_source_occupation'] or '',
                source_name=row['salary_source_name'] or '',year=row['salary_reference_year'] or '',
                measure=row['salary_measure'] or '',match_type=row['salary_match_type'] or '',
                mapping_note=row['salary_mapping_note'] or '',median=row['salary_median'],
                reviewed_on=row['salary_reviewed_on'] or ''),
            wfh_info=work_arrangement(row),is_wfh_capable=bool(row['is_wfh_capable']),
            onet_url='https://www.onetonline.org/link/summary/'+row['onet_code'],reference_note=note,
            fit_reasons=build_fit_reasons(row,scores,skills,goal,education,allowed_zones,matched),
            fit_evidence=build_fit_evidence(row,scores,matched),
            fit_cautions=build_fit_cautions(row,scores,goal),
            interest_profile={trait:float(row[column]) for trait,column in zip('RIASEC',RIASEC_COLUMNS)}))
    return candidates
