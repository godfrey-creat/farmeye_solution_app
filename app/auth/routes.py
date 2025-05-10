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
    register_form = RegistrationForm()  # Create registration form instance
    
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data.lower()).first()
        
        if user is None:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/auth.html',
                              login_form=login_form,
                              register_form=register_form,
                              active_tab='login')
        
        if not user.verify_password(login_form.password.data):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/auth.html',
                              login_form=login_form,
                              register_form=register_form,
                              active_tab='login')
        
        if not user.is_approved:
            flash('Your account is pending approval. Please try again later.', 'warning')
            return render_template('auth/auth.html',
                              login_form=login_form,
                              register_form=register_form,
                              active_tab='login')
        
        login_user(user, login_form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()

        flash('Login successful! Welcome back.', 'success')
        
        # Get the next page from the request args, or default to dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('farm.dashboard')
            
        return redirect(next_page)

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
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        flash("You're already logged in.", "info")
        return redirect(url_for('farm.dashboard'))

    login_form = LoginForm()
    register_form = RegistrationForm()
    
    if request.method == 'POST':
        # Print form data for debugging
        print("Form submitted with data:", flush=True)
        for field, value in register_form.data.items():
            if field != 'csrf_token' and field != 'password' and field != 'confirm_password':
                print(f"{field}: {value}", flush=True)
        
        # Check form validation explicitly
        if not register_form.validate():
            print("Form validation failed:", flush=True)
            for fieldname, errors in register_form.errors.items():
                print(f"Field '{fieldname}' has errors: {errors}", flush=True)
                # Also flash these errors to the user
                for error in errors:
                    flash(f"{fieldname}: {error}", "danger")
            
            # Return the form with validation errors
            return render_template('auth/auth.html', 
                              login_form=login_form,
                              register_form=register_form, 
                              active_tab='register')
        
        # If we get here, form validation succeeded
        print("Form validation succeeded, creating user...", flush=True)
        
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == register_form.email.data.lower()) |
                (User.username == register_form.username.data)
            ).first()
            
            if existing_user:
                if existing_user.email == register_form.email.data.lower():
                    flash('Email is already registered.', 'danger')
                else:
                    flash('Username is already taken.', 'danger')
                return render_template('auth/auth.html',
                                  login_form=login_form,
                                  register_form=register_form,
                                  active_tab='register')

            # Create new user
            user = User(
                email=register_form.email.data.lower(),
                username=register_form.username.data,
                password=register_form.password.data,
                first_name=register_form.first_name.data,
                last_name=register_form.last_name.data,
                phone_number=register_form.phone_number.data,
                user_type=register_form.user_type.data,
                region=register_form.region.data,
                is_approved=True  # Set to True for now, can be changed based on requirements
            )

            db.session.add(user)
            db.session.commit()
            print("User created successfully!", flush=True)

            # Log the user in automatically
            login_user(user)
            flash('Registration successful! Welcome to FarmEye.', 'success')
            return redirect(url_for('farm.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}", flush=True)
            flash('An error occurred during registration. Please try again.', 'danger')
    
    # GET request or form validation failed
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