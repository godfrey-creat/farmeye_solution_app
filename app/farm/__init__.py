# app/farm/__init__.py
from flask import Blueprint

farm = Blueprint('farm', __name__)

from . import routes