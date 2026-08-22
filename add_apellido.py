import sqlalchemy
from database import engine
from sqlalchemy import text

def run_alter():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN apellido VARCHAR;"))
            try:
                conn.commit()
            except:
                pass
            print("Columna apellido añadida correctamente.")
        except sqlalchemy.exc.ProgrammingError as e:
            if "already exists" in str(e):
                print("La columna ya existe.")
            else:
                print(f"Error: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")

if __name__ == "__main__":
    run_alter()
