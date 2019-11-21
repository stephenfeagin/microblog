import os
from typing import Iterable, List, Optional

from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    """The config object stores configuration settings for the Flask app"""

    SECRET_KEY: str = os.environ.get("SECRET_KEY") or "you-will-never-guess"

    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    LANGUAGES: List[str] = ["en", "es"]
    MS_TRANSLATOR_KEY = os.environ.get("MS_TRANSLATOR_KEY")
    POSTS_PER_PAGE: int = 10

    # SQLAlchemy setup
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
        basedir, "app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Mail server setup
    MAIL_SERVER: Optional[str] = os.environ.get("MAIL_SERVER")
    MAIL_PORT: int = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS: bool = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME: Optional[str] = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD: Optional[str] = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER: str = os.environ.get("MAIL_DEFAULT_SENDER") or f"noreply@{MAIL_SERVER}"
    ADMINS: Iterable[str] = ("stephenfeagin@example.com",)
