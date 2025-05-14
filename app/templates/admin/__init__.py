from flask import Flask
from .models import db  # Import db here

def create_app():
    app = Flask(__name__)
    
    # Initialize the app with the db
    app.config.from_object('config.Config')
    db.init_app(app)

    # Register blueprints
    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    return app
