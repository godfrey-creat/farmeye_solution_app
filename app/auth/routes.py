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
from urllib.parse import urlparse

csrf = CSRFProtect()

@auth.route('/')
def index():
    """Auth index redirects to login"""
    return redirect(url_for('auth.login'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('farm.dashboard'))

    login_form = LoginForm()
    register_form = RegistrationForm()  # Create an instance of the registration form
    
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data.lower()).first()
        if user and user.verify_password(login_form.password.data):
            login_user(user, login_form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('farm.dashboard'))

        flash('Invalid email or password. Please try again or '
              '<a href="{}">reset your password</a>.'.format(url_for('auth.reset_password_request')),
              'danger')

    # Pass both forms to the template
    return render_template('auth/auth.html', 
                           login_form=login_form,
                           register_form=register_form, 
                           active_tab='login')

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        flash("You're already logged in.", "info")
        return redirect(url_for('farm.dashboard'))

    login_form = LoginForm()  # Create an instance of the login form
    register_form = RegistrationForm()
    
    if register_form.validate_on_submit():
        # Create new user logic...
        
        # Redirect to login page
        return redirect(url_for('auth.login'))

    # Pass both forms to the template
    return render_template('auth/auth.html', 
                           login_form=login_form,
                           register_form=register_form, 
                           active_tab='register')

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request"""
    if current_user.is_authenticated:
        return redirect(url_for('farm.dashboard'))
    
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
        return redirect(url_for('farm.dashboard'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('The reset link is invalid or has expired.', 'danger')
            return redirect(url_for('auth.reset_password_request'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

@auth.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('auth/profile.html')