"""Production HTTP entry point; configure HTTPS at the hosting proxy."""
import os
import logging
from waitress import serve
from wsgi import application
from app.db import database_connection

def main():
    with database_connection(application.config['DATABASE']) as db:
        if not db.execute('SELECT COUNT(*) FROM occupations').fetchone()[0]:
            raise SystemExit('Run python manage.py initialize-database before serving.')
    logging.basicConfig(level=logging.INFO)
    serve(application, host=os.environ.get('HOST','127.0.0.1'),
        port=int(os.environ.get('PORT','8080')), threads=int(os.environ.get('WEB_THREADS','4')),
        max_request_body_size=65536, expose_tracebacks=False)

if __name__ == '__main__':
    main()
