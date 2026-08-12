from database import engine
from sqlalchemy import text

with engine.connect() as connection:
    try:
        connection.execute(text("ALTER TABLE employees ADD COLUMN cedula VARCHAR;"))
        connection.commit()
        print("Column 'cedula' added successfully.")
    except Exception as e:
        print("Error adding column:", e)
