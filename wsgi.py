"""WSGI application for production servers: wsgi:application."""
from app import create_app
application = create_app()
