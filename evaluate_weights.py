"""Offline comparison of ranking weights; never changes live scoring or user records."""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from app.config import DB_PATH
from app.recommendation.engine import RankingWeights, DEFAULT_WEIGHTS, recommend_career
from app.services.assessment import score_responses

CANDIDATES = {
    'current': DEFAULT_WEIGHTS,
    'interests_only': RankingWeights(interest=1, education_penalty=0, skill_per_match=0,
                                    skill_cap=0, goal_multiplier=0, feedback_multiplier=0),
    'stronger_context': RankingWeights(education_penalty=20, skill_per_match=5),
    'lighter_context': RankingWeights(education_penalty=10, skill_per_match=3),
}


def prepare_profiles(profiles, db):
    seen = set()
    participants = {}
    prepared = []
    for profile in profiles:
        identity = profile.get('profile_id')
        participant = profile.get('participant_code')
        split = profile.get('split')
        if not isinstance(identity,str) or not identity or identity in seen:
            raise ValueError('Each profile needs a unique nonempty profile_id.')
        if not isinstance(participant,str) or not participant or split not in ('development','test'):
            raise ValueError('Use a participant_code and a development or test split.')
        if participant in participants and participants[participant] != split:
            raise ValueError('A participant cannot appear in both development and test sets.')
        participants[participant] = split
        seen.add(identity)
        scores = score_responses(profile['answers'])
        rankings = {name:recommend_career(profile['goal'],profile['education'],scores,
                     profile.get('skills',[]),db,weights, use_feedback=False)[:5]
                    for name,weights in CANDIDATES.items()}
        prepared.append((profile,rankings))
    if not prepared:
        raise ValueError('Supply at least one profile.')
    return prepared


def review_pool(prepared):
    pool = []
    for profile,rankings in prepared:
        unique = {job['code']:job for jobs in rankings.values() for job in jobs}
        pool.append({**profile, 'ratings':profile.get('ratings',{}),
            'review_pool':[{'code':code,'title':job['title'],'description':job['description']}
                           for code,job in sorted(unique.items())]})
    return pool


def evaluate(prepared):
    splits = {profile['split'] for profile,_ in prepared}
    if splits != {'development','test'}:
        raise ValueError('Provide separate development and held-out test participants.')
    report = {'status':'comparison_only_not_automatic_validation',
              'feedback_used':False, 'weights':{n:asdict(w) for n,w in CANDIDATES.items()},
              'splits':{}}
    for profile,rankings in prepared:
        ratings = profile.get('ratings',{})
        pool = {j['code'] for jobs in rankings.values() for j in jobs}
        missing = pool - ratings.keys()
        if missing:
            raise ValueError(f"Profile {profile['profile_id']} has unreviewed careers: {', '.join(sorted(missing))}. Export the review pool first.")
        if any(isinstance(v,bool) or not isinstance(v,int) or v not in range(4) for v in ratings.values()):
            raise ValueError('Ratings must be integers: 0 irrelevant, 1 somewhat relevant, 2 relevant, 3 very relevant.')
        ideal = sorted((ratings[code] for code in pool), reverse=True)[:5]
        ideal_dcg = sum((2**value-1)/math.log2(i+2) for i,value in enumerate(ideal))
        split = report['splits'].setdefault(profile['split'],{})
        for name,jobs in rankings.items():
            values = [ratings[job['code']] for job in jobs]
            if len(values)!=5: raise ValueError('The catalog must contain at least five careers.')
            precision = sum(value>=2 for value in values)/5
            dcg = sum((2**value-1)/math.log2(i+2) for i,value in enumerate(values))
            split.setdefault(name,[]).append({'profile_id':profile['profile_id'],
                'precision_at_5':precision,'ndcg_at_5':dcg/ideal_dcg if ideal_dcg else None})
    for split in report['splits'].values():
        for name,rows in list(split.items()):
            defined = [r['ndcg_at_5'] for r in rows if r['ndcg_at_5'] is not None]
            split[name] = {'profiles':len(rows),
                'mean_precision_at_5':sum(r['precision_at_5'] for r in rows)/len(rows),
                'mean_ndcg_at_5':sum(defined)/len(defined) if defined else None,
                'ndcg_defined_profiles':len(defined),'per_profile':rows}
    report['notes'] = [
        'Use development results to choose settings; evaluate the chosen setting once on held-out participants.',
        'nDCG uses the union of reviewed top-five careers, not the entire occupation catalog.',
        'Ratings of 2 or 3 count as relevant for Precision@5. Missing judgments are rejected, not treated as irrelevant.',
        'Feedback is disabled for all settings to prevent evaluation labels leaking through community boosts.',
        'Keep learner and expert judgments in separate datasets. These metrics do not measure career success or questionnaire reliability.',
        'Small samples are exploratory. Report participant counts and disagreement; do not claim statistical superiority from averages alone.']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles',required=True,type=Path)
    parser.add_argument('--database',type=Path,default=DB_PATH)
    parser.add_argument('--export-pool',type=Path)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    profiles = json.loads(args.profiles.read_text())
    # Read-only mode guarantees this evaluation cannot change production data.
    db = sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        prepared = prepare_profiles(profiles,db)
        result = review_pool(prepared) if args.export_pool else evaluate(prepared)
        if not args.export_pool:
            result['dataset_sha256'] = hashlib.sha256(args.profiles.read_bytes()).hexdigest()
            result['catalog_sha256'] = hashlib.sha256(json.dumps([tuple(row) for row in db.execute('SELECT * FROM occupations ORDER BY onet_code')]).encode()).hexdigest()
        text = json.dumps(result,indent=2)+'\n'
        destination = args.export_pool or args.output
        if destination:
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_text(text)
            print('Written:',destination)
        else:
            print(text)
    except (ValueError,KeyError,TypeError) as error:
        parser.error(str(error))
    finally:
        db.close()

if __name__ == '__main__':
    main()
