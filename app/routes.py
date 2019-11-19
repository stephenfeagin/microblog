"""app/routes.py"""
from datetime import datetime
from typing import Optional

from flask import flash, g, jsonify, redirect, render_template, request, url_for
from flask_babel import _, get_locale
from flask_login import current_user, login_required, login_user, logout_user
from flask_sqlalchemy import Pagination
from guess_language import guess_language
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from werkzeug.urls import url_parse

from app import app, db
from app.email import send_password_reset_email
from app.forms import (
    EditProfileForm,
    LoginForm,
    PostForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
)
from app.models import Post, User
from app.translate import translate


@app.before_request
def before_request():
    """
    Common functionality to be processed before every request. Updates user's last_seen.

    TODO: Update to only overwrite last_seen in the database if last_seen is earlier than today
    - This might not work nicely because of time zone conversion -- could be the same day
    locally but different days in UTC, or vice-versa
    - But I don't like having a database write on every single request by a logged-in user
    - Could do if last_seen is greater than an hour old
    - Or just if last_seen UTC is earlier than today UTC
    """

    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        try:
            db.session.commit()
        except (DBAPIError, SQLAlchemyError):
            db.session.rollback()
    g.locale = str(get_locale())


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    """Home page view"""

    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == "UNKNOWN" or len(language) > 5:
            language = ""
        post = Post(body=form.post.data, author=current_user, language=language)
        try:
            db.session.add(post)
            db.session.commit()
        except (DBAPIError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(_("Could not process your post, please try again!"))
            app.logger.error(e)
        else:
            flash(_("Your post is now live!"))
        return redirect(url_for("index"))

    page = request.args.get("page", default=1, type=int)
    posts: Pagination = current_user.followed_posts().paginate(
        page, app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for("index", page=posts.next_num) if posts.has_next else None
    prev_url: Optional[str] = url_for("index", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html",
        title=_("Home"),
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login view"""

    # if user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_("Invalid username or password"))
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")

        # check for valid ?next query param and re-assign if necessary
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(url_for("index"))

    return render_template("login.html", title=_("Sign In"), form=form)


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
            flash(_("Could not complete user registration, please try again!"))
            return redirect(url_for("register"))

        flash("Congratulations, you are now a registered member!")
        return redirect(url_for("login"))

    return render_template("register.html", title=_("Register"), form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    """User profile view"""

    user: User = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", default=1, type=int)
    posts: Pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for(
        "user", username=user.username, page=posts.next_num
    ) if posts.has_next else None
    prev_url: Optional[str] = url_for(
        "user", username=user.username, page=posts.prev_num
    ) if posts.has_prev else None
    return render_template(
        "user.html", user=user, posts=posts.items, next_url=next_url, prev_url=prev_url
    )


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
            flash(_("Could not edit user profile, please try again!"))
            app.logger.error(e)
        else:
            flash(_("Your changes have been saved."))
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title=_("Edit Profile"), form=form)


@app.route("/follow/<username>")
@login_required
def follow(username):
    """Endpoint for following another user"""
    user: Optional[User] = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("User %(username)s not found.", username=username))
        return redirect(url_for("index"))
    if user == current_user:
        flash(_("You cannot follow yourself!"))
        return redirect(url_for("user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_("You are now following %(username)s!", username=username))
    return redirect(url_for("user", username=username))


@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    """Endpoint for unfollowing another user"""
    user: Optional[User] = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("User %(username)s not found.", username=username))
        return redirect(url_for("index"))
    if user == current_user:
        flash(_("You cannot unfollow yourself!"))
        return redirect(url_for("user", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_("You are no longer following %(username)s.", username=username))
    return redirect(url_for("user", username=username))


@app.route("/explore")
@login_required
def explore():
    """View for displaying recent posts by all users"""

    page = request.args.get("page", default=1, type=int)
    posts: Pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for("index", page=posts.next_num) if posts.has_next else None
    prev_url: Optional[str] = url_for("index", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html", title=_("Explore"), posts=posts.items, next_url=next_url, prev_url=prev_url,
    )


@app.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user: Optional[User] = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            send_password_reset_email(user)
        flash(_("Check your email for the instructions to reset your password"))
        return redirect(url_for("login"))
    return render_template("reset_password_request.html", title=_("Reset Password"), form=form)


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """View for resetting a user's password with a token"""

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user: Optional[User] = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_("Your password has been reset."))
        return redirect(url_for("login"))
    return render_template("reset_password.html", title=_("Reset password"), form=form)


@app.route("/translate", methods=["POST"])
@login_required
def translate_text():
    """Translates text from a POST form and serializes it into a JSON object"""
    return jsonify(
        {
            "text": translate(
                request.form["text"], request.form["source_language"], request.form["dest_language"]
            )
        }
    )
