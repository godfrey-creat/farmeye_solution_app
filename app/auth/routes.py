# app/auth/routes.py
from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from . import auth
from .forms import (
    LoginForm,
    RegistrationForm,
    RequestResetPasswordForm,
    ResetPasswordForm,
)
from .models import User
from .. import db
from ..utils.email import send_email
from urllib.parse import urlparse, urlsplit
from ..farm.models import Farm  # Add this import

csrf = CSRFProtect()


@auth.route("/")
def index():
    """Auth index redirects to login"""
    return redirect(url_for("auth.login"))


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Log in an existing user"""
    if current_user.is_authenticated:
        # Check if user has any farms
        has_farms = Farm.query.filter_by(user_id=current_user.id).first() is not None
        if not has_farms:
            # Redirect to farm registration if no farms
            return redirect(url_for("farm.register_farm"))
        return redirect(url_for("farm.dashboard"))

    form = LoginForm()
    register_form = RegistrationForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.verify_password(form.password.data):
            flash("Invalid email or password", "error")
            return render_template(
                "auth/auth.html",
                login_form=form,
                register_form=register_form,
                active_tab="login",
            )

        login_user(user, remember=form.remember_me.data)

        # After login, check if user has any farms
        has_farms = Farm.query.filter_by(user_id=user.id).first() is not None
        if not has_farms:
            # Redirect to farm registration if no farms
            return redirect(url_for("farm.register_farm"))

        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("farm.dashboard")
        return redirect(next_page)

    return render_template(
        "auth/auth.html",
        login_form=form,
        register_form=register_form,
        active_tab="login",
    )


@auth.route("/logout")
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user"""
    if current_user.is_authenticated:
        # Check if user has any farms
        has_farms = Farm.query.filter_by(user_id=current_user.id).first() is not None
        if not has_farms:
            return redirect(url_for("farm.register_farm"))
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    login_form = LoginForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone_number.data,
            user_type=form.user_type.data,
            region=form.region.data,
        )
        user.password = form.password.data  # Use the password property setter
        db.session.add(user)
        db.session.commit()

        # Log the user in after registration
        login_user(user)

        # Redirect to farm registration
        return redirect(url_for("farm.register_farm"))

    return render_template(
        "auth/auth.html",
        register_form=form,
        login_form=login_form,
        active_tab="register",
    )


@auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """Handle password reset request"""
    if current_user.is_authenticated:
        return redirect(url_for("farm.dashboard"))

    form = RequestResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(
                user.email,
                "Reset Your Password",
                "auth/email/reset_password",
                user=user,
                token=token,
            )
        flash(
            "An email with instructions to reset your password has been sent to you.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password_request.html", form=form)


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for("farm.dashboard"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash("Your password has been updated.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("The reset link is invalid or has expired.", "danger")
            return redirect(url_for("auth.reset_password_request"))

    return render_template("auth/reset_password.html", form=form, token=token)


@auth.route("/profile")
@login_required
def profile():
    """Display user profile"""
    return render_template("auth/profile.html")
