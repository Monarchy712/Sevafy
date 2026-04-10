import os
import sys
from sqlalchemy.orm import Session
from uuid import uuid4

# Setup path to include the current directory so we can import 'app'
sys.path.append(os.getcwd())

from app import models
from app.database import SessionLocal

def seed_personnel():
    db = SessionLocal()
    try:
        # 1. Fetch all NGO personnel users
        print("Fetching NGO_PERSONNEL users...")
        users = db.query(models.User).filter(models.User.role == models.UserRole.NGO_PERSONNEL).order_by(models.User.email).all()
        if len(users) < 5:
            print(f"Warning: Found only {len(users)} NGO personnel users, expected 5.")
        else:
            print(f"Found {len(users)} users.")

        # 2. Fetch all NGOs
        print("Fetching NGOs...")
        ngos = db.query(models.NGO).order_by(models.NGO.name).all()
        if len(ngos) < 5:
            print(f"Warning: Found only {len(ngos)} NGOs, expected 5.")
        else:
            print(f"Found {len(ngos)} NGOs.")

        # 3. Link them (one-to-one)
        # We will link users and NGOs in sorted order of their identifiers
        # Users sorted by email, NGOs sorted by name
        
        limit = min(len(users), len(ngos))
        print(f"\nLinking {limit} users to NGOs...")

        for i in range(limit):
            user = users[i]
            ngo = ngos[i]

            # Check if this link already exists
            existing_link = db.query(models.NGOPersonnel).filter(
                models.NGOPersonnel.user_id == user.id,
                models.NGOPersonnel.ngo_id == ngo.id
            ).first()

            if existing_link:
                print(f" [SKIP] {user.email} is already linked to {ngo.name}")
            else:
                print(f" [LINK] {user.email} -> {ngo.name}")
                new_link = models.NGOPersonnel(
                    id=uuid4(),
                    user_id=user.id,
                    ngo_id=ngo.id
                )
                db.add(new_link)

        db.commit()
        print("\nSeeding complete!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_personnel()
