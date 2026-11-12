"""WSGI application for production servers: wsgi:application."""
# wsgi.py (at the root of your repository)
from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run()
