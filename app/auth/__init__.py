"""
app/auth/__init__.py
"""
from flask import Blueprint


bp = Blueprint("auth", __name__)

from . import email, forms, routes  # noqa: E402,F401
