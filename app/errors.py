"""
app/errors.py
"""
from flask import render_template

from app import app, db


@app.errorhandler(404)
def not_found_error(error):
    """Delivers custom 404 Error page"""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Rolls back database session and returns a 500 Internal Server Error page"""
    db.session.rollback()
    return render_template("500.html"), 500
