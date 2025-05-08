# app/auth/routes.py
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from . import auth
from .forms import LoginForm, RegistrationForm, RequestResetPasswordForm, ResetPasswordForm
from .models import User
from .. import db
from ..utils.email import send_email

csrf = CSRFProtect()

@auth.route('/')
def index():
    return render_template('auth/index.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))  # Redirect authenticated user to the home page

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('auth.home'))  # Redirect to home view

        # Flash error and suggest password reset
        flash('Invalid email or password. Please try again or '
              '<a href="{}">reset your password</a>.'.format(url_for('auth.reset_password_request')),
              'danger')

    return render_template('auth/home.html', form=form)




@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        flash("You're already logged in.", "info")
        return redirect(url_for('auth.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            user_type=form.user_type.data,
            is_approved=False  # Default to not approved
        )

        db.session.add(user)
        db.session.commit()

        # Flash registration success message
        flash('Registration successful! Please log in.', 'success')

        # Redirect to login page
        return redirect(url_for('auth.login'))

    return render_template('auth/auth.html', form=form)



@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(
                user.email,
                'Reset Your Password',
                'auth/email/reset_password',
                user=user,
                token=token
            )
        flash('An email with instructions to reset your password has been sent to you.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('auth.reset_password_request'))
    
    return render_template('auth/reset_password.html', form=form)


@auth.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('auth/profile.html')