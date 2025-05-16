<<<<<<< HEAD
# app/admin/__init__.py
from flask import Blueprint

admin = Blueprint('admin', __name__)

=======
# app/admin/__init__.py
from flask import Blueprint

admin = Blueprint('admin', __name__)

# Import routes at the end to avoid circular imports
>>>>>>> origin/Dynamic-Parsing
from . import routes