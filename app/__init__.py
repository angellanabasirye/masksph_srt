# app/__init__.py

from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from app.extensions import db  
from app.admin import admin_bp 
import os
basedir = os.path.abspath(os.path.dirname(__file__))


migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:12345@localhost:5432/masksph_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main
    app.register_blueprint(main)

    app.register_blueprint(admin_bp, url_prefix='/admin')

    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')  
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from app.seed import seed_bp
    app.register_blueprint(seed_bp)

    return app

