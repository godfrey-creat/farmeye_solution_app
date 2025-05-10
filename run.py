import os
from app import create_app, db
from app.auth.models import User
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'development')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """Make database objects available in Flask shell"""
    return dict(db=db, User=User)

if __name__ == '__main__':
    app.run(debug=True)