# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from .models import User

class LoginForm(FlaskForm):
    """Form for user login"""
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    """Form for user registration"""
    email = StringField('Email', validators=[
        DataRequired(), 
        Length(1, 64),
        Email()
    ])
    username = StringField('Username', validators=[
        DataRequired(),
        Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must start with a letter and can only contain '
               'letters, numbers, dots or underscores')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(), 
        Length(1, 64)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(), 
        Length(1, 64)
    ])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(10, 15)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('password2', message='Passwords must match.')
    ])
    password2 = PasswordField('Confirm password', validators=[
        DataRequired()
    ])
    submit = SubmitField('Register')

    def validate_email(self, field):
        """Validate that email is not already registered"""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        """Validate that username is not already in use"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class FarmRegistrationForm(FlaskForm):
    """Form for registering a new farm"""
    name = StringField('Farm Name', validators=[
        DataRequired(), 
        Length(1, 100)
    ])
    location = StringField('Location', validators=[
        DataRequired(), 
        Length(1, 200)
    ])
    size_acres = FloatField('Size (acres)', validators=[
        DataRequired()
    ])
    crop_type = StringField('Primary Crop Type', validators=[
        DataRequired(), 
        Length(1, 100)
    ])
    description = TextAreaField('Description')
    submit = SubmitField('Register Farm')


class RequestResetPasswordForm(FlaskForm):
    """Form for requesting password reset"""
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """Form for resetting password"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')