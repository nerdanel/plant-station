from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    NumberRange,
)
from app.models import User, Device


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username is taken, please choose a different one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "Account with this email already exists. Try logging in or reset your password."
            )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class UpdateProfileForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    "Username is taken, please choose a different one."
                )

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    "Account with this email already exists. Try logging in or reset your password."
                )


class NewDeviceForm(FlaskForm):
    serial_no = StringField(
        "Serial no.", validators=[DataRequired(), Length(min=2, max=30)]
    )
    nickname = StringField("Nickname", validators=[DataRequired()])

    submit = SubmitField("Add Device")

    def validate_serial(self, serial_no):
        device = Device.query.filter_by(serial_no=serial_no.data).first()
        if device:
            raise ValidationError("Device already registered!")


class DeviceConfigForm(FlaskForm):
    moisture_threshold = IntegerField(
        "Moisture threshold (1-100)",
        validators=[DataRequired(), NumberRange(min=1, max=100)],
    )
    water_volume_ml = IntegerField(
        "Water volume (ml)", validators=[DataRequired(), NumberRange(min=10, max=1000)]
    )
    frequency_min = IntegerField(
        "Measurement frequency (min)",
        validators=[DataRequired(), NumberRange(min=5, max=180)],
    )

    submit = SubmitField("Update Settings")


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("Email account not found. Please register first.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")
