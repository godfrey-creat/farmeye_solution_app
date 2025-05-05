# app/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user
from .auth.models import Permission

def permission_required(permission):
    """Decorator for checking if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator for checking if user is an admin"""
    return permission_required(Permission.ADMIN)(f)

def farmer_only(f):
    """Decorator for checking if user is a farmer"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_farmer():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function