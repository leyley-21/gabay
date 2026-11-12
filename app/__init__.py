# app/__init__.py (at the root of the app folder)
# Inside your routes or blueprint file (e.g., app/routes.py or app/__init__.py)
from flask import render_template

@app.route('/')
def home():
    # Return your home HTML template or a welcome message
    return render_template('index.html') # or return "Welcome to ALS Gabay!"
