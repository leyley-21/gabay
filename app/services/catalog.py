"""Validated, atomic imports; requests never fall back to CSV or hardcoded pathways."""
import csv
from app.services.salary import SALARY_COLUMNS
from datetime import date
from urllib.parse import urlsplit
from app.config import REFERENCE_DIR, RIASEC_COLUMNS
from app.db import database_connection

def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))

def import_catalog(path=None, source=None):
    raw = read_csv(source or REFERENCE_DIR / 'occupation_catalog.csv')
    rows = []
    for row in raw:
        features = [float(row[c]) for c in RIASEC_COLUMNS]
        if any(not 1 <= value <= 7 for value in features):
            raise ValueError('O*NET interest scores must be between 1 and 7.')
        rows.append((row['onet_code'], row['title'], row['description'], int(row['job_zone']),
            '', '', row.get('wfh_info', ''), '',
            int(row.get('is_wfh_capable', '').lower() in ('true','1','yes')), *features))
    if not rows or len({r[0] for r in rows}) != len(rows):
        raise ValueError('Catalog must have unique, nonempty occupation rows.')
    with database_connection(path) as db:
        db.executemany("""INSERT INTO occupations
            (onet_code,title,description,job_zone,college_majors,tech_voc,wfh_info,salary,
             is_wfh_capable,realistic,investigative,artistic,social,enterprising,conventional)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(onet_code) DO UPDATE SET
            title=excluded.title,description=excluded.description,job_zone=excluded.job_zone,
            wfh_info=excluded.wfh_info,is_wfh_capable=excluded.is_wfh_capable,
            realistic=excluded.realistic,investigative=excluded.investigative,artistic=excluded.artistic,
            social=excluded.social,enterprising=excluded.enterprising,conventional=excluded.conventional""", rows)
    return len(rows)

def import_references(path=None, directory=None):
    directory = directory or REFERENCE_DIR
    specifications = {
        'college_programs': ('programs',), 'tesda_programs': ('qualifications',),
        'salary_ranges': SALARY_COLUMNS}
    prepared = {}
    for table, extra in specifications.items():
        records = read_csv(directory / (table + '.csv'))
        if table == 'salary_ranges':
            from app.services.salary import prepare_salary
            for row in records:prepare_salary(row)
        seen = set()
        for row in records:
            code = row['onet_code'].strip()
            if not code or code in seen:
                raise ValueError(f'{table}: duplicate or missing occupation code.')
            seen.add(code)
            if row['data_status'] not in ('legacy_estimate','curated','verified','unavailable'):
                raise ValueError(f'{table}: invalid data_status.')
            if row['source_url'] and (urlsplit(row['source_url']).scheme != 'https' or not urlsplit(row['source_url']).netloc):
                raise ValueError(f'{table}: source_url must be an HTTPS URL.')
            if row['reviewed_on']:
                date.fromisoformat(row['reviewed_on'])
            if row['data_status'] == 'verified' and not (row['source_url'] and row['reviewed_on']):
                raise ValueError(f'{table}: verified rows need a source URL and review date.')
        if not records:
            raise ValueError(f'{table}: file is empty; no changes were made.')
        cols = ['onet_code', *extra, 'country','data_status','source_url','reviewed_on']
        prepared[table] = (cols, [tuple(row[c] for c in cols) for row in records])
    # The optional CSV catalog validates names; school/program SQL tables are retired.
    registry_file=directory/'program_catalog.csv'
    if registry_file.exists():
        registry=read_csv(registry_file)
        valid={(r['kind'],r['name'].casefold()) for r in registry}
        for table,kind in [('college_programs','college'),('tesda_programs','tesda')]:
            for row in prepared[table][1]:
                for name in (p.strip() for p in row[1].split('|')):
                    if name and (kind,name.casefold()) not in valid:raise ValueError(f'{table}: unknown catalog program: {name}')
    with database_connection(path) as db:
        for table, (cols, rows) in prepared.items():
            db.execute('DELETE FROM '+table)
            db.executemany(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", rows)
        # Keep historical occupation display columns consistent with the canonical tables.
        db.execute("""UPDATE occupations SET
            college_majors=COALESCE((SELECT programs FROM college_programs c WHERE c.onet_code=occupations.onet_code),''),
            tech_voc=COALESCE((SELECT qualifications FROM tesda_programs t WHERE t.onet_code=occupations.onet_code),''),
            salary=COALESCE((SELECT salary_display FROM salary_ranges s WHERE s.onet_code=occupations.onet_code),'')""")
    return {table:len(rows) for table, (_, rows) in prepared.items()}
