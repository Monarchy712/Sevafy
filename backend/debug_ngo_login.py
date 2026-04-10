import os
import traceback
from dotenv import load_dotenv

# Setup path
import sys
sys.path.append(os.getcwd())

load_dotenv()

from app import models, auth, schemas
from app.database import SessionLocal

def debug_login():
    db = SessionLocal()
    try:
        user_email = 'bt25csh048@iiitn.ac.in'
        password = 'pwd123'
        
        print(f"DEBUG: Attempting login for {user_email}")
        user = db.query(models.User).filter(models.User.email == user_email).first()
        if not user:
            print("ERROR: User not found in DB")
            return
            
        print(f"DEBUG: User found: {user.full_name} (Role: {user.role})")
        
        # Check password
        print("DEBUG: Verifying password...")
        is_valid = auth.verify_password(password, user.password)
        print(f"DEBUG: Password valid: {is_valid}")
        
        # Create token
        print("DEBUG: Creating access token...")
        token = auth.create_access_token(data={"sub": user.email, "role": user.role.value})
        print(f"DEBUG: Token created: {token[:15]}...")
        
        print("\nDEBUG: Attempting to call /ngo/stats logic...")
        from app.ngo_router import _get_ngo_for_user, get_ngo_stats_live
        
        ngo = _get_ngo_for_user(user, db)
        print(f"DEBUG: NGO found: {ngo.name} (UID: {ngo.blockchain_uid})")
        
        stats = get_ngo_stats_live(user, db)
        print(f"DEBUG: Stats fetched successfully: {stats.ngo_name}")

    except Exception as e:
        print("\n!!! ERROR CAUGHT !!!")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_login()
