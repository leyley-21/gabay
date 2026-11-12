"""Rebuild occupation evidence from the three bundled raw O*NET source CSVs."""
import csv
from app.config import ONET_SOURCE_DIR, REFERENCE_DIR, RIASEC_COLUMNS
from app.services.catalog import read_csv, import_catalog


def rebuild_onet_catalog(path=None):
    profiles = {}
    for row in read_csv(ONET_SOURCE_DIR / 'career_interest_types.csv'):
        if row['Scale ID'] != 'OI':
            continue
        trait = row['Element Name'].lower()
        if trait in RIASEC_COLUMNS:
            profiles.setdefault(row['O*NET-SOC Code'], {})[trait] = float(row['Data Value'])
    occupations = {r['O*NET-SOC Code']:r for r in read_csv(ONET_SOURCE_DIR / 'occupation_data.csv')}
    zones = {r['O*NET-SOC Code']:int(r['Job Zone']) for r in read_csv(ONET_SOURCE_DIR / 'job_zones.csv')}
    previous = {r['onet_code']:r for r in read_csv(REFERENCE_DIR / 'occupation_catalog.csv')}
    rows = []
    for code, features in sorted(profiles.items()):
        if code not in occupations or len(features) != 6:
            raise ValueError(f'Incomplete O*NET occupation evidence: {code}')
        old = previous.get(code, {})
        rows.append(dict(onet_code=code,title=occupations[code]['Title'],description=occupations[code]['Description'],
            job_zone=zones.get(code,2),wfh_info=old.get('wfh_info','Remote-work information not available.'),
            is_wfh_capable=old.get('is_wfh_capable','false'),**features))
    if not rows:
        raise ValueError('No usable OI profiles found; existing catalog retained.')
    output = REFERENCE_DIR / 'occupation_catalog.csv'
    staging = output.with_suffix('.pending.csv')
    with staging.open('w',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Validate and commit DB update before publishing the new seed CSV.
    count = import_catalog(path, staging)
    staging.replace(output)
    return count
