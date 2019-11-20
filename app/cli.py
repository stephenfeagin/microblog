"""
app/cli.py
"""
import os

import click
from flask import Flask


def register(app: Flask) -> None:
    """Register CLI commands"""

    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    def babel_extract() -> None:
        """Run pybabel extract.

        Raises:
            RuntimeError: If the command returns a non-zero exit status, raise a RuntimeError

        Returns:
            None
        """
        if os.system("pybabel extract -F babel.cfg -k _l -o messages.pot ."):
            raise RuntimeError("extract command failed")

    @translate.command()
    @click.argument("lang")
    def init(lang: str):
        """Initialize a new language."""
        babel_extract()
        if os.system(f"pybabel init -i messages.pot -d app/translations -l {lang}"):
            raise RuntimeError("init command failed")
        os.remove("messages.pot")

    @translate.command()
    def update():
        """Update all languages."""
        babel_extract()
        if os.system("pybabel update -i messages.pot -d app/translations"):
            raise RuntimeError("update command failed")
        os.remove("messages.pot")

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system("pybabel compile -d app/translations"):
            raise RuntimeError("compile command failed")
