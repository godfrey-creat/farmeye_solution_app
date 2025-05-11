# app/farm/__init__.py
from flask import Blueprint

farm = Blueprint('farm', __name__)

# Import routes at the end to avoid circular imports
# Models should be imported first by the blueprint consumers
from . import models
from . import routes  # Import routes after models