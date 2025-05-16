# app/admin/__init__.py
from flask import Blueprint

admin = Blueprint('admin', __name__)

# Import routes at the end to avoid circular imports
from . import routes