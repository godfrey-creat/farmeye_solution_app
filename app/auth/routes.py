# app/auth/routes.py
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from . import auth
from .forms import LoginForm, RegistrationForm, RequestResetPasswordForm, ResetPasswordForm
from .models import User, Role, Permission
from .. import db
from ..utils.email import send_email

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            if not user.is_approved:
                flash('Your account is pending approval. Please wait for an admin to approve it.', 'warning')
                return redirect(url_for('auth.login'))
            
            login_user(user, form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to the page the user was trying to access or to the dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                if user.is_admin():
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('farm.dashboard')
            return redirect(next_page)
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data
        )
        
        # Set role to farmer (default) or admin if it's the first user
        if User.query.count() == 0:
            user.role = Role.query.filter_by(name='Admin').first()
            user.is_approved = True
        else:
            user.role = Role.query.filter_by(name='Farmer').first()
            user.is_approved = False
            
        db.session.add(user)
        db.session.commit()
        
        # Send notification to admins about new user registration
        if not user.is_approved:
            admins = User.query.join(Role).filter(Role.name == 'Admin').all()
            for admin in admins:
                send_email(
                    admin.email,
                    'New User Registration',
                    'auth/email/new_user',
                    user=user,
                    admin=admin
                )
            
        flash('Registration successful! ' + 
              ('Your account is now active.' if user.is_approved else 
               'Your account is pending approval by an administrator.'), 
              'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


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