import os

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

from models.student_model import create_table
from routes.export_routes import export_bp
from routes.bug_check_routes import bug_check_bp
from routes.student_routes import student_bp
from routes.upload_routes import upload_bp
from routes.auth_routes import auth_bp


load_dotenv()

session_database = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL must be set before starting the application')
    session_database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    if not app.config['SECRET_KEY']:
        raise RuntimeError('SECRET_KEY must be set before starting the application')
    app.config['SQLALCHEMY_DATABASE_URI'] = session_database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    session_database.init_app(app)
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = session_database
    app.config['SESSION_SQLALCHEMY_TABLE'] = 'flask_sessions'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('RENDER'))
    Session(app)

    try:
        create_table()
        app.logger.info('PostgreSQL database initialized')
    except Exception as error:
        app.logger.exception('PostgreSQL database initialization failed')
        raise RuntimeError('PostgreSQL database initialization failed') from error

    app.register_blueprint(student_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(bug_check_bp)
    app.register_blueprint(auth_bp)
    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
