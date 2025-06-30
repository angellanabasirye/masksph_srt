import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Define upload paths
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'milestones')
BULK_UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'bulk_students')


class Config:
    # App security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'masksph_secret_key'

    # Database connection
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost:5432/masksph_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload paths
    UPLOAD_FOLDER = UPLOAD_FOLDER
    BULK_UPLOAD_FOLDER = BULK_UPLOAD_FOLDER
