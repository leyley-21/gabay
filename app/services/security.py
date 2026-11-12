"""Signed anonymous sessions, CSRF protection and shared SQLite request budgets."""
import hashlib
import hmac
import os
import secrets
import time
from datetime import timedelta
from pathlib import Path
from flask import current_app, jsonify, request, session
from app.db import get_db


def configure_security(app):
    secret = os.environ.get('GABAY_SECRET_KEY')
    if not secret:
        # Persist locally so cookies survive restarts. Never ship this generated key.
        key_path = Path(app.config['DATABASE']).parent / '.session-secret'
        key_path.parent.mkdir(parents=True, exist_ok=True)
        if not key_path.exists():
            temporary = key_path.with_name('.session-secret.' + secrets.token_hex(8))
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, 'w') as handle:
                    handle.write(secrets.token_hex(32))
                # Publish only the complete key; concurrent workers share the winner.
                try:
                    os.link(temporary, key_path)
                except FileExistsError:
                    pass
            finally:
                temporary.unlink(missing_ok=True)
        secret = key_path.read_text().strip()
    app.config.update(SECRET_KEY=secret, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.environ.get('GABAY_COOKIE_SECURE') == '1',
                      PERMANENT_SESSION_LIFETIME=timedelta(days=7),
                      SESSION_REFRESH_EACH_REQUEST=False,
                      RATE_LIMITS={'session_issue': (120, 600), 'predict_ip': (60, 60),
                                   'predict_session': (12, 60), 'feedback_ip': (180, 60),
                                   'feedback_session': (40, 60), 
                                   'location_ip': (60,60), 'location_session': (12,60),
                                   'report_ip': (30,60), 'report_session': (6,60)})

    @app.before_request
    def protect_requests():
        if request.endpoint == 'main.home' and 'anonymous_id' not in session:
            denied = consume_limits([('session_issue', ip_subject())])
            if denied: return denied
            session['anonymous_id'] = secrets.token_urlsafe(24)
            session['csrf_token'] = secrets.token_urlsafe(32)
            session.permanent = True
        if request.endpoint not in ('main.predict', 'main.log_feedback','main.resolve_location','main.career_report'):
            return None
        if not session.get('anonymous_id'):
            return jsonify(status='error', message='Please refresh the page before continuing.'), 403
        supplied = request.headers.get('X-CSRF-Token', '')
        if not supplied or not hmac.compare_digest(supplied, session.get('csrf_token', '')):
            return jsonify(status='error', message='Please refresh the page before continuing.'), 403
        action = {'main.predict':'predict','main.log_feedback':'feedback',
                  'main.resolve_location':'location', 'main.career_report':'report'}[request.endpoint]
        return consume_limits([(action+'_ip', ip_subject()),
                               (action+'_session', session['anonymous_id'])])

    @app.context_processor
    def anonymous_context():
        return {'anonymous_id': session.get('anonymous_id', ''),
                'csrf_token': session.get('csrf_token', '')}


def ip_subject():
    # Do not trust arbitrary X-Forwarded-For headers. Configure a trusted proxy
    # explicitly if deployed behind one; otherwise limits share the proxy IP.
    address = request.remote_addr or 'unknown'
    return hmac.new(current_app.secret_key.encode(), address.encode(), hashlib.sha256).hexdigest()


def consume_limits(subjects):
    now = int(time.time())
    db = get_db()
    with db:
        # Serialize increments across workers, not merely within one process.
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM request_limits WHERE bucket < ?', (now - 1200,))
        for scope, subject in subjects:
            limit, seconds = current_app.config['RATE_LIMITS'][scope]
            bucket = now // seconds * seconds
            db.execute("""INSERT INTO request_limits(scope,subject,bucket,count) VALUES (?,?,?,1)
                ON CONFLICT(scope,subject,bucket) DO UPDATE SET count=count+1""", (scope,subject,bucket))
            count = db.execute('SELECT count FROM request_limits WHERE scope=? AND subject=? AND bucket=?',
                               (scope,subject,bucket)).fetchone()[0]
            if count > limit:
                response = jsonify(status='error', message='Too many requests. Please wait a moment and try again.')
                response.status_code = 429
                response.headers['Retry-After'] = str(max(1, bucket + seconds - now))
                return response
    return None
