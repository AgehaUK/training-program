"""初期ユーザー投入スクリプト"""
from app.core.auth import get_password_hash
from app.db.database import SessionLocal
from app.models.user import User


def seed():
    db = SessionLocal()
    try:
        initial_users = [
            {"username": "admin", "password": "admin1234", "role": "admin"},
            {"username": "user1", "password": "user1234", "role": "user"},
        ]
        for u in initial_users:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if not exists:
                user = User(
                    username=u["username"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                )
                db.add(user)
                print(f"Created user: {u['username']} ({u['role']})")
            else:
                print(f"User already exists: {u['username']}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
