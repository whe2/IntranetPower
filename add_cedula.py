import database
from database import engine
from models import Base
import sqlalchemy

def migrate():
    # Attempt to add cedula column. If it exists, it will throw an exception which we catch.
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text('ALTER TABLE employees ADD COLUMN cedula VARCHAR'))
            print("Column 'cedula' added successfully.")
    except Exception as e:
        print("Column 'cedula' may already exist or error occurred:", e)
        
    # Create all missing tables (e.g. departments)
    Base.metadata.create_all(bind=engine)
    print("Database synced successfully.")

if __name__ == "__main__":
    migrate()
