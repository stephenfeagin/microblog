from datetime import datetime
from typing import Union

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


class User(UserMixin, db.Model):
    """SQLAlchemy model for Users. Inherits from flask_login.UserMixin."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship("Post", backref="author", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        """Hashes provided password and sets the output to the password_hash field"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks whether the provided password is valid for the user's password hash"""
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id: Union[str, int]) -> User:
    """Looks up a user by ID. Used as the user_loader for flask_login."""
    try:
        int_id = int(id)
    except ValueError:
        raise ValueError("Invalid user ID provided: Must be convertible to integer")
    return User.query.get(int_id)


class Post(db.Model):
    """SQLAlchemy model for blog posts"""

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<Post {self.body}>"
