from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Connect to the database and drop the temporary table
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS _alembic_tmp_task_recurrences"))
        conn.commit()

    print("Temporary table dropped successfully.") 