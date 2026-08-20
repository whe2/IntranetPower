import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import User

def main():
    db = SessionLocal()
    try:
        active_users = db.query(User).filter(User.is_active == True).all()
        if not active_users:
            print("No active users found.")
            return

        print(f"Found {len(active_users)} active users:")
        for user in active_users:
            print(f"- Username: {user.username}, Email: {user.email}, Name: {user.full_name}, Role: {user.role}")
    except Exception as e:
        print(f"Error connecting to database or querying users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
