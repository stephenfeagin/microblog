"""
app/auth/forms.py
"""

from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

from app.models import User


class LoginForm(FlaskForm):
    """WTForms class for user login"""

    username = StringField(_l("Username"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember Me"))
    submit = SubmitField(_l("Sign In"))


class RegistrationForm(FlaskForm):
    """WTForms class for user registration"""

    username = StringField(_l("Username"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Register"))

    def validate_username(self, username):
        """Ensure there is no other user with the provided username"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_("Please use a different username."))

    def validate_email(self, email):
        """Ensure there is no other user with the provided email"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_("Please use a different email address."))


class ResetPasswordForm(FlaskForm):
    """WTForms class for resetting a user's password"""

    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Reset Password"))


class ResetPasswordRequestForm(FlaskForm):
    """WTForms class for requesting a password reset"""

    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Request Password Reset"))
