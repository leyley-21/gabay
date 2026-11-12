# app/__init__.py (at the root of the app folder)
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app
