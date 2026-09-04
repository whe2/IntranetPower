import sys
from database import SessionLocal
from models import User
from security import get_password_hash

def main():
    if len(sys.argv) < 3:
        print("Uso: python reset_password.py <email_del_usuario> <nueva_contraseña>")
        sys.exit(1)

    email = sys.argv[1]
    new_password = sys.argv[2]

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()

    if not user:
        print(f"Error: Usuario con correo '{email}' no encontrado.")
        sys.exit(1)

    user.hashed_password = get_password_hash(new_password)
    db.commit()
    print(f"¡Éxito! Contraseña actualizada para {email}.")

if __name__ == "__main__":
    main()
