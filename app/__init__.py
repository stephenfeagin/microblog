"""
app/__init__.py
"""
import logging
import os
from logging.handlers import RotatingFileHandler, SMTPHandler
from typing import Optional

from elasticsearch import Elasticsearch
from flask import current_app, Flask, request
from flask_babel import Babel, lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from config import Config


# Plugin initialization
db = SQLAlchemy()
migrate = Migrate()
babel = Babel()
bootstrap = Bootstrap()
login = LoginManager()
moment = Moment()
mail = Mail()

login.login_view = "auth.login"
login.login_message = _l("Please log in to access this page.")


@babel.localeselector
def get_locale() -> Optional[str]:
    """Attempts to identify the best match for the user's locale based on the entries in the
    LANGUAGES config
    """
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


def create_app(config_class: Config = Config) -> Flask:
    """App factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register plugins with the app
    db.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)
    bootstrap.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)

    # Register Elasticsearch as an instance attribute
    app.elasticsearch: Optional[Elasticsearch] = (
        Elasticsearch([app.config["ELASTICSEARCH_URL"]])
        if app.config["ELASTICSEARCH_URL"]
        else None
    )

    # Register blueprints
    from .auth import bp as auth_bp
    from .errors import bp as errors_bp
    from .main import bp as main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(errors_bp)
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:

        # Email error logging
        if app.config["MAIL_SERVER"]:
            auth = None
            # TODO: convert these if statements to try/except
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="noreply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="Microblog Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        # File error logging

        # stdout logging (heroku logs) or file logging
        if app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists("logs"):
                os.mkdir("logs")
            file_handler = RotatingFileHandler("logs/microblog.log", maxBytes=10240, backupCount=10)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Microblog startup")

    return app


from app import models  # noqa: E402,F401
