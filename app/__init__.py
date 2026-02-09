from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Register Blueprints
    from app.routes import auth, main, decks, classes, study, cards
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(decks.bp)
    app.register_blueprint(classes.bp)
    app.register_blueprint(study.bp)
    app.register_blueprint(cards.bp)

    return app
