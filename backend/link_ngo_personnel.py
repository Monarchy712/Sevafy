import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.append(os.getcwd())

from app import models
from app.database import SessionLocal

def fix():
    db = SessionLocal()
    try:
        # 1. Get the first NGO (or create one if missing)
        ngo = db.query(models.NGO).first()
        if not ngo:
            print("Creating a default NGO...")
            ngo = models.NGO(
                name="Sunrise Education Foundation",
                description="Dedicated to empowering students.",
                bank_account_number="1234567890",
                bank_ifsc_code="SYNB0001234",
                upi_id="sunrise@okaxis"
            )
            db.add(ngo)
            db.commit()
            db.refresh(ngo)

        print(f"Using NGO: {ngo.name} (ID: {ngo.id}, UID: {ngo.blockchain_uid})")

        # 2. Find all NGO_PERSONNEL users
        users = db.query(models.User).filter(models.User.role == "NGO_PERSONNEL").all()
        print(f"Found {len(users)} NGO Personnel users.")

        for u in users:
            # Check if linked
            link = db.query(models.NGOPersonnel).filter(models.NGOPersonnel.user_id == u.id).first()
            if not link:
                print(f"Linking User {u.email} to NGO {ngo.name}...")
                new_link = models.NGOPersonnel(user_id=u.id, ngo_id=ngo.id)
                db.add(new_link)
        
        db.commit()
        print("Done.")

    finally:
        db.close()

if __name__ == "__main__":
    fix()
