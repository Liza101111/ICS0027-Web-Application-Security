from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=80)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8)
        ]
    )

    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


class LogoutForm(FlaskForm):
    submit = SubmitField("Logout")

class UploadForm(FlaskForm):
    file = FileField(
        "Choose file",
        validators=[DataRequired()]
    )

    submit = SubmitField("Upload")

class DeleteForm(FlaskForm):
    submit = SubmitField("Delete")