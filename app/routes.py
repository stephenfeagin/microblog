"""app/routes.py"""
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from werkzeug.urls import url_parse

from app import app, db
from app.forms import EditProfileForm, LoginForm, RegistrationForm
from app.models import User


@app.before_request
def before_request():
    """
    Common functionality to be processed before every request. Updates user's last_seen.

    TODO: Update to only overwrite last_seen in the database if last_seen is earlier than today
    - This might not work nicely because of time zone conversion -- could be the same day
    locally but different days in UTC, or vice-versa
    - But I don't like having a database write on every single request by a logged-in user
    """

    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        try:
            db.session.commit()
        except (DBAPIError, SQLAlchemyError):
            db.session.rollback()


@app.route("/")
@app.route("/index")
@login_required
def index():
    """Home page view"""

    posts = [
        {"author": {"username": "John"}, "body": "Beautiful day in Portland!"},
        {"author": {"username": "Susan"}, "body": "The Avengers movie was so cool!"},
    ]
    return render_template("index.html", title="Home", posts=posts)


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login view"""

    # if user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")

        # check for valid ?next query param and re-assign if necessary
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(url_for("index"))

    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    """User logout view. Redirects user to home page."""

    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration view"""

    # if user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
        except (DBAPIError, SQLAlchemyError):
            db.session.rollback()
            flash("Could not complete user registration, please try again!")
            return redirect(url_for("register"))

        flash("Congratulations, you are now a registered member!")
        return redirect(url_for("login"))

    return render_template("register.html", title="Regiser", form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    """User profile view"""

    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {"author": user, "body": "Test post #1"},
        {"author": user, "body": "Test post #2"},
    ]

    return render_template("user.html", user=user, posts=posts)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """User profile editing view"""

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        try:
            db.session.commit()
        except (DBAPIError, SQLAlchemyError) as e:
            db.session.rollback()
            flash("Could not edit user profile, please try again!")
            app.logger.error(e)
        else:
            flash("Your changes have been saved.")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.route("/follow/<username>")
@login_required
def follow(username):
    """Endpoint for following another user"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f"User {username} not found.")
        return redirect(url_for("index"))
    if user == current_user:
        flash("You cannot follow yourself!")
        return redirect(url_for("user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f"You are now following {username}!")
    return redirect(url_for("user", username=username))


@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    """Endpoint for unfollowing another user"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f"User {username} not found.")
        return redirect(url_for("index"))
    if user == current_user:
        flash("You cannot unfollow yourself!")
        return redirect(url_for("user", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f"You are no longer following {username}.")
    return redirect(url_for("user", username=username))
