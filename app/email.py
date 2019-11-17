from threading import Thread
from typing import List, Optional

from flask import Flask, render_template
from flask_mail import Message

from app import app, mail
from app.models import User


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
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user: User) -> None:
    """Send a given user a password reset token"""

    token = user.get_reset_password_token()
    send_email(
        "[Microblog] Reset Your Password",
        sender=app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template("email/reset_password.txt.j2", user=user, token=token),
        html_body=render_template("email/reset_password.html", user=user, token=token),
    )
