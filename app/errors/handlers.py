"""
app/errors.py
"""
from flask import render_template

from app import db

from . import bp


@bp.errorhandler(404)
def not_found_error(error):
    """Delivers custom 404 Error page"""
    return render_template("errors/404.html"), 404


@bp.errorhandler(500)
def internal_error(error):
    """Rolls back database session and delivers a 500 Internal Server Error page"""
    db.session.rollback()
    return render_template("errors/500.html"), 500
