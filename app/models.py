"""
app/models.py
"""
from datetime import datetime
from hashlib import md5
from time import time
from typing import Optional, List, Tuple, Union

import jwt
from flask import current_app
from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery
from sqlalchemy.orm.session import Session
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login
from .search import add_to_index, query_index, remove_from_index


class SearchableMixin:
    """Implements common functionality for Elasticsearch integration"""

    __searchable__: List[str] = []

    @classmethod
    def search(cls, expression: str, page: int, per_page: int) -> Tuple[BaseQuery, int]:
        """Run an Elasticsearch query and return the database objects"""
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if not total:
            return cls.query.filter_by(id=0), 0
        when = [(ids[i], i) for i in range(len(ids))]
        return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session: Session) -> None:
        """Registers session changes in a _changes dict"""
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted),
        }

    @classmethod
    def after_commit(cls, session: Session) -> None:
        """
        Reads from the session._changes dict and updates the Elasticsearch index for affected
        objects
        """
        for obj in session._changes["add"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["update"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["delete"]:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        """Indexes or re-indexes all objects in cls"""
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


# Register event handlers
db.event.listen(db.session, "before_commit", SearchableMixin.before_commit)
db.event.listen(db.session, "after_commit", SearchableMixin.after_commit)


followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)


class User(UserMixin, db.Model):
    """SQLAlchemy model for Users. Inherits from flask_login.UserMixin."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password: str) -> None:
        """Hashes provided password and sets the output to the password_hash field"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks whether the provided password is valid for the user's password hash"""
        return check_password_hash(self.password_hash, password)

    def avatar(self, size: Union[str, int]) -> str:
        """Returns the URL for a user's Gravatar image"""
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=retro&s={size}"

    def is_following(self, user) -> bool:
        """Indicates whether user is in the parent object's `followed` list"""
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def follow(self, user) -> None:
        """Adds user to parent object's `followed` list"""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user) -> None:
        """Removes user from parent object's `followed` list"""
        try:
            self.followed.remove(user)
        except ValueError:
            pass

    def followed_posts(self):
        """Fetches posts written by users in the parent object's `followed` list"""
        followed = Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(
            followers.c.follower_id == self.id
        )
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        """Provides a password reset token for a given user.

        :param expires_in: How long the token is valid, in seconds, defaults to 600
        :type expires_in: int

        :return: JSON Web Token for the user's password request
        :rtype: str
        """

        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token: str) -> Optional["User"]:
        """Looks up a user referenced by a JWT password reset token, or returns None if there is an
        error decoding the JWT.

        :param token: JWT password reset token
        :type token: str

        :return: User object, or None
        :rtype: Optional[User]
        """

        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])[
                "reset_password"
            ]
        except jwt.PyJWTError as e:
            current_app.logger.info(e)
            return
        return User.query.get(id)


@login.user_loader
def load_user(id: Union[str, int]) -> User:
    """Looks up a user by ID. Used as the user_loader callback for flask_login."""
    return User.query.get(int(id))


class Post(SearchableMixin, db.Model):
    """SQLAlchemy model for blog posts"""

    __searchable__ = ["body"]

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    language = db.Column(db.String(5))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<Post {self.body}>"
