from flask import Blueprint

weather = Blueprint('weather', __name__)

from . import routes  # Import routes after creating the Blueprint to avoid circular imports 