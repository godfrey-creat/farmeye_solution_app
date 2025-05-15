from flask import Blueprint

irrigation = Blueprint("irrigation", __name__)

from app.irrigation import routes, models
