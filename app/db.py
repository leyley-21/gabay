"""The sole SQLite connection factory used by routes and command-line tools."""
import sqlite3
from contextlib import contextmanager
from flask import current_app, g
from app.config import DB_PATH

def connect_database(path=None):
    path = path or DB_PATH
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def database_connection(path=None):
    conn = connect_database(path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def get_db():
    if 'db' not in g:
        g.db = connect_database(current_app.config['DATABASE'])
    return g.db

def close_db(error=None):
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()
