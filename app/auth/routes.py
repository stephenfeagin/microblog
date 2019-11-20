"""
app/auth/routes.py
"""
from typing import Optional

from flask import flash, redirect, render_template, request, url_for
from flask_babel import _
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from werkzeug.urls import url_parse

from app import db
from app.models import User

from . import bp
from .email import send_password_reset_email
from .forms import LoginForm, RegistrationForm, ResetPasswordForm, ResetPasswordRequestForm


@bp.route("/login", methods=["GET", "POST"])
def login():
    """User login view"""

    # if user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid username or password"))
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")

        # check for valid ?next query param and re-assign if necessary
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.index")
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", title=_("Sign In"), form=form)


@bp.route("/logout")
def logout():
    """User logout view. Redirects user to home page."""

    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration view"""

    # if user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
        except (DBAPIError, SQLAlchemyError):
            db.session.rollback()
            flash(_("Could not complete user registration, please try again!"))
            return redirect(url_for("auth.register"))

        flash("Congratulations, you are now a registered member!")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title=_("Register"), form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            send_password_reset_email(user)
        flash(_("Check your email for the instructions to reset your password"))
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password_request.html", title=_("Reset Password"), form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """View for resetting a user's password with a token"""

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user: Optional[User] = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for("main.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_("Your password has been reset."))
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", title=_("Reset password"), form=form)
