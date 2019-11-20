from threading import Thread
from typing import List, Optional

from flask import current_app, Flask
from flask_mail import Message

from . import mail


def send_async_email(app: Flask, msg: Message) -> None:
    with app.app_context():
        mail.send(msg)


def send_email(
    subject: str = "",
    sender: Optional[str] = None,
    recipients: Optional[List[str]] = None,
    text_body: Optional[str] = None,
    html_body: Optional[str] = None,
) -> None:
    """Send an email with Flask-Mail"""

    msg = Message(subject=subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
