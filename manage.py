"""Administrative commands. Run `python manage.py --help` for the command list."""
import argparse
from app.config import DB_PATH
from app.schema import initialize_database
from app.db import database_connection
from app.services.catalog import import_catalog, import_references
from app.services.feedback import rebuild_summary


def initialize():
    initialize_database()
    with database_connection() as db:
        empty = not db.execute('SELECT COUNT(*) FROM occupations').fetchone()[0]
    if empty:
        print(f'Imported {import_catalog()} occupations.')
    print('Reference imports:', import_references())
    with database_connection() as db:
        print('Feedback groups:', rebuild_summary(db))
    print('Database ready:', DB_PATH)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['initialize-database','import-reference-data','import-onet-data',
        'refresh-feedback-summary','show-statistics'])
    args = parser.parse_args()
    if args.command == 'initialize-database':
        initialize()
    elif args.command == 'import-reference-data':
        print(import_references())
    elif args.command == 'import-onet-data':
        from app.services.onet_import import rebuild_onet_catalog
        print('Imported occupations:', rebuild_onet_catalog())
    elif args.command == 'refresh-feedback-summary':
        with database_connection() as db:
            print('Feedback groups:', rebuild_summary(db))
    elif args.command == 'show-statistics':
        with database_connection() as db:
            for table in ('occupations','college_programs','tesda_programs','salary_ranges','quiz_attempts','raw_feedback_logs','job_feedback_summary'):
                print(f'{table}: {db.execute("SELECT COUNT(*) FROM "+table).fetchone()[0]}')

if __name__ == '__main__':
    main()
