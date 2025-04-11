import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'masksph_secret_key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://angella:mypassword@localhost/masksph_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
