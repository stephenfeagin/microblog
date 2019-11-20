"""
app/translate.py
"""

import json

import requests
from flask import current_app
from flask_babel import _


def translate(text: str, source_language: str, dest_language: str) -> str:
    """Issue an call to the Microsoft API to translate the provided text"""
    if "MS_TRANSLATOR_KEY" not in current_app.config or not current_app.config["MS_TRANSLATOR_KEY"]:
        return _("Error: the translation service is not configured.")
    auth = {"Ocp-Apim-Subscription-Key": current_app.config["MS_TRANSLATOR_KEY"]}
    r = requests.get(
        f"https://api.microsofttranslator.com/v2/Ajax.svc/Translate?text={text}"
        f"&from={source_language}&to={dest_language}",
        headers=auth,
    )
    if r.status_code != 200:
        return _("Error: the translation service failed")
    return json.loads(r.content.decode("utf-8-sig"))
