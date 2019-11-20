"""
app/routes.py
"""
from datetime import datetime
from typing import Optional

from flask import current_app, flash, g, jsonify, redirect, render_template, request, url_for
from flask_babel import _, get_locale
from flask_login import current_user, login_required
from flask_sqlalchemy import Pagination
from guess_language import guess_language
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from app import db
from app.models import Post, User
from app.translate import translate

from . import bp
from .forms import EditProfileForm, PostForm


@bp.before_request
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


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
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
            current_app.logger.error(e)
        else:
            flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))

    page = request.args.get("page", default=1, type=int)
    posts: Pagination = current_user.followed_posts().paginate(
        page, current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for("main.index", page=posts.next_num) if posts.has_next else None
    prev_url: Optional[str] = url_for("main.index", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html",
        title=_("Home"),
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/explore")
@login_required
def explore():
    """View for displaying recent posts by all users"""

    page = request.args.get("page", default=1, type=int)
    posts: Pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for("main.index", page=posts.next_num) if posts.has_next else None
    prev_url: Optional[str] = url_for("main.index", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html", title=_("Explore"), posts=posts.items, next_url=next_url, prev_url=prev_url,
    )


@bp.route("/user/<username>")
@login_required
def user(username):
    """User profile view"""

    user: User = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", default=1, type=int)
    posts: Pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    next_url: Optional[str] = url_for(
        "main.user", username=user.username, page=posts.next_num
    ) if posts.has_next else None
    prev_url: Optional[str] = url_for(
        "main.user", username=user.username, page=posts.prev_num
    ) if posts.has_prev else None
    return render_template(
        "user.html", user=user, posts=posts.items, next_url=next_url, prev_url=prev_url
    )


@bp.route("/edit_profile", methods=["GET", "POST"])
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
            current_app.logger.error(e)
        else:
            flash(_("Your changes have been saved."))
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template("edit_profile.html", title=_("Edit Profile"), form=form)


@bp.route("/follow/<username>")
@login_required
def follow(username):
    """Endpoint for following another user"""
    user: Optional[User] = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("User %(username)s not found.", username=username))
        return redirect(url_for("main.index"))
    if user == current_user:
        flash(_("You cannot follow yourself!"))
        return redirect(url_for("main.user", username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_("You are now following %(username)s!", username=username))
    return redirect(url_for("main.user", username=username))


@bp.route("/unfollow/<username>")
@login_required
def unfollow(username):
    """Endpoint for unfollowing another user"""
    user: Optional[User] = User.query.filter_by(username=username).first()
    if user is None:
        flash(_("User %(username)s not found.", username=username))
        return redirect(url_for("main.index"))
    if user == current_user:
        flash(_("You cannot unfollow yourself!"))
        return redirect(url_for("main.user", username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_("You are no longer following %(username)s.", username=username))
    return redirect(url_for("main.user", username=username))


@bp.route("/translate", methods=["POST"])
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
