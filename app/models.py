from datetime import datetime
from hashlib import md5
from typing import Union

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login


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
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())


@login.user_loader
def load_user(id: Union[str, int]) -> User:
    """Looks up a user by ID. Used as the user_loader callback for flask_login."""
    return User.query.get(int(id))


class Post(db.Model):
    """SQLAlchemy model for blog posts"""

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<Post {self.body}>"
