<<<<<<< HEAD
# app/auth/__init__.py
from flask import Blueprint

auth = Blueprint('auth', __name__)

# Import models first
from . import models
# Then import routes, which might depend on models
=======
# app/auth/__init__.py
from flask import Blueprint

auth = Blueprint('auth', __name__)

# Import models first
from . import models
# Then import routes, which might depend on models
>>>>>>> origin/Dynamic-Parsing
from . import routes