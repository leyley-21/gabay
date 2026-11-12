from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Define your routes inside the factory function here:
    @app.route('/')
    def home():
        return "Welcome to ALS Gabay!"
    
    # Set any required config if needed (like your database)
    app.config['DATABASE'] = '/var/lib/als_gabay/als_gabay.db'
    
    return app
