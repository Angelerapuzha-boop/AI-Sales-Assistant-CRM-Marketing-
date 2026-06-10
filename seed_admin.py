#!/usr/bin/env python3
"""Initialize database and seed admin user."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models import User, UserRole
from app.utils.security import get_password_hash


def main():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@aisales.com").first()
        if not admin:
            admin = User(
                email="admin@aisales.com",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="System Admin",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            db.commit()
            print("Admin user created: admin@aisales.com / Admin@123456")
        else:
            print("Admin user already exists")
    finally:
        db.close()


if __name__ == "__main__":
    main()
