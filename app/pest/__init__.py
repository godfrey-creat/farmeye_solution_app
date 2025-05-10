from flask import Blueprint

pest = Blueprint('pest', __name__)

from . import routes 