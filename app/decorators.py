# app/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user


def farmer_only(f):
    """Decorator for checking if user is a farmer"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_approved:  # Ensure the user is approved
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function