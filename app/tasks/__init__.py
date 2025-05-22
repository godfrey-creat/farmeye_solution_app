from flask import Blueprint

task = Blueprint('task', __name__)

# Import routes at the bottom to avoid circular imports
from app.tasks import routes