import unittest
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Post, User
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username="susan")
        u.set_password("cat")
        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_avatar(self):
        u = User(username="john", email="john@example.com")
        result = "https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=retro&s=128"
        self.assertEqual(u.avatar(128), result)

    def test_follow(self):
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertListEqual(u1.followed.all(), [])
        self.assertListEqual(u2.followed.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, "susan")
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, "john")

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        john = User(username="john", email="john@example.com")
        susan = User(username="susan", email="susan@example.com")
        mary = User(username="mary", email="mary@example.com")
        david = User(username="david", email="david@example.com")
        db.session.add_all([john, susan, mary, david])

        # create four posts
        now = datetime.utcnow()
        john_post = Post(body="post from john", author=john, timestamp=now + timedelta(seconds=1))
        susan_post = Post(
            body="post from susan", author=susan, timestamp=now + timedelta(seconds=4)
        )
        mary_post = Post(body="post from mary", author=mary, timestamp=now + timedelta(seconds=3))
        david_post = Post(
            body="post from david", author=david, timestamp=now + timedelta(seconds=2)
        )
        db.session.add_all([john_post, susan_post, mary_post, david_post])
        db.session.commit()

        # set up follows
        john.follow(susan)
        john.follow(david)
        susan.follow(mary)
        mary.follow(david)
        db.session.commit()

        # check followed posts
        j_followed_posts = john.followed_posts().all()
        s_followed_posts = susan.followed_posts().all()
        m_followed_posts = mary.followed_posts().all()
        d_followed_posts = david.followed_posts().all()
        self.assertListEqual(j_followed_posts, [susan_post, david_post, john_post])
        self.assertListEqual(s_followed_posts, [susan_post, mary_post])
        self.assertListEqual(m_followed_posts, [mary_post, david_post])
        self.assertListEqual(d_followed_posts, [david_post])


if __name__ == "__main__":
    unittest.main(verbosity=2)
