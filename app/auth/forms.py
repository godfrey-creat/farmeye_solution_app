from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.auth.models import db  # Import db directly here, but defer User import


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    region = SelectField('Region', choices=[
        ('nairobi', 'Nairobi'),
        ('central', 'Central'),
        ('coast', 'Coast'),
        ('eastern', 'Eastern'),
        ('north-eastern', 'North Eastern'),
        ('nyanza', 'Nyanza'),
        ('rift-valley', 'Rift Valley'),
        ('western', 'Western')
    ], validators=[DataRequired()])
    user_type = SelectField('User Type', choices=[
        ('small-scale', 'Small-Scale'),
        ('large-scale', 'Large-Scale'),
        ('cooperative', 'Cooperative')
    ], validators=[DataRequired()])  # Added dropdown for user type
    submit = SubmitField('Register')

    def validate_email(self, email):
        from app.auth.models import User  # Deferred import
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email is already registered.')

    def validate_username(self, username):
        from app.auth.models import User  # Deferred import
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken.')


class RequestResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        from app.auth.models import User  # Deferred import
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is None:
            raise ValidationError('No account is associated with this email.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')