from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email address is required"),
        Email(message="Enter a valid email address"),
        Length(max=120)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField("Remember Me")


class RegistrationForm(FlaskForm):
    name = StringField("Full Name", validators=[
        DataRequired(message="Full name is required"),
        Length(min=2, max=80, message="Name must be between 2 and 80 characters")
    ])
    email = StringField("Email Address", validators=[
        DataRequired(message="Email address is required"),
        Email(message="Enter a valid email address"),
        Length(max=120)
    ])
    phone = StringField("Mobile Number", validators=[
        DataRequired(message="Mobile number is required"),
        Regexp(r"^\d{10}$", message="Enter a valid 10-digit mobile number")
    ])
    city = StringField("City", validators=[
        DataRequired(message="Please select or enter your city"),
        Length(max=50)
    ])
    password = PasswordField("Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=8, max=64, message="Password must be between 8 and 64 characters"),
        Regexp(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", message="Password must contain uppercase, lowercase, and a number")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])


class OtpForm(FlaskForm):
    otp_code = StringField("OTP", validators=[
        DataRequired(message="OTP is required"),
        Regexp(r"^\d{6}$", message="Enter the 6-digit code")
    ])


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[
        DataRequired(message="Email address is required"),
        Email(message="Enter a valid email address"),
        Length(max=120)
    ])


class ResetPasswordForm(FlaskForm):
    otp_code = StringField("OTP Code", validators=[
        DataRequired(message="OTP is required"),
        Regexp(r"^\d{6}$", message="Enter the 6-digit code")
    ])
    password = PasswordField("New Password", validators=[
        DataRequired(message="Password is required"),
        Length(min=8, max=64, message="Password must be between 8 and 64 characters"),
        Regexp(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", message="Password must contain uppercase, lowercase, and a number")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo("password", message="Passwords must match")
    ])
