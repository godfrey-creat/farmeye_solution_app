from flask import Blueprint

advisory = Blueprint("advisory", __name__)

from app.advisory import routes, models
