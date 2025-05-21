# app/decorators.py
from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user
from app.farm.models import Farm


def farmer_only(f):
    """Decorator for checking if user is a farmer"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_approved:  # Ensure the user is approved
            abort(403)  # Forbidden
        return f(*args, **kwargs)

    return decorated_function


def require_farm_registration(f):
    """Decorator to ensure user has registered a farm before accessing the page"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        has_farm = Farm.query.filter_by(user_id=current_user.id).first() is not None
        if not has_farm:
            return redirect(url_for("farm.register_farm"))

        return f(*args, **kwargs)

    return decorated_function
