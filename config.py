import os


class Config:
    """The config object stores configuration settings for the Flask app"""

    SECRET_KEY: str = os.environ.get("SECRET_KEY") or "you-will-never-guess"
