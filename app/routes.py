"""app/routes.py"""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User


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
