import os
import sys
import bcrypt
from sqlalchemy.orm import Session

# Setup path
sys.path.append(os.getcwd())

from app import models, auth
from app.database import SessionLocal

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def fix_users():
    db = SessionLocal()
    try:
        # 1. Update passwords for all NGO personnel to 'pwd123'
        print("Checking NGO personnel passwords...")
        ngo_users = db.query(models.User).filter(models.User.role == models.UserRole.NGO_PERSONNEL).all()
        hashed_pwd = get_password_hash("pwd123")
        
        for u in ngo_users:
            if u.password is None:
                print(f" [FIX] Setting password for {u.email}")
                u.password = hashed_pwd
            else:
                print(f" [PASS] {u.email} already has a password")
        
        db.commit()
        print("Password update complete.")

        # 2. Re-verify linkage
        print("\nVerifying NGO personnel links...")
        # Get NGOs (the 5 new ones)
        ngos = db.query(models.NGO).order_by(models.NGO.name).all()
        # Sort users to ensure deterministic mapping
        ngo_users.sort(key=lambda x: x.email)
        
        limit = min(len(ngo_users), len(ngos))
        for i in range(limit):
            user = ngo_users[i]
            ngo = ngos[i]
            
            # Check if linked
            link = db.query(models.NGOPersonnel).filter(models.NGOPersonnel.user_id == user.id).first()
            if not link:
                print(f" [LINK] {user.email} -> {ngo.name}")
                new_link = models.NGOPersonnel(
                    user_id=user.id,
                    ngo_id=ngo.id
                )
                db.add(new_link)
            elif link.ngo_id != ngo.id:
                print(f" [UPDATE] {user.email} currently linked to {db.query(models.NGO).get(link.ngo_id).name}. Re-linking to {ngo.name}...")
                link.ngo_id = ngo.id
            else:
                print(f" [OK] {user.email} is correctly linked to {ngo.name}")

        db.commit()
        print("Linkage verification complete!")

    except Exception as e:
        db.rollback()
        print(f"Error during fix: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_users()
