import sys
import traceback
import os
import uuid
sys.path.append(os.path.abspath('c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend'))
from app.database import SessionLocal
from app import models, auth, schemas

try:
    db = SessionLocal()
    # Get any DONATOR user
    user = db.query(models.User).filter_by(role=models.UserRole.DONATOR).first()
    if not user:
        print("No donator user found")
        sys.exit(0)
        
    ngo = db.query(models.NGO).first()
    if not ngo:
        print("No ngo found")
        sys.exit(0)
        
    profile = db.query(models.DonatorProfile).filter_by(user_id=user.id).first()
    
    donation = models.Donation(
        donator_id=profile.id,
        ngo_id=ngo.id,
        amount=5000,
        remaining_amount=5000,
        confirmed=True,
        tx_hash="SIMULATED_SUCCESS",
    )
    db.add(donation)
    
    profile.has_donated = True
    profile.total_donated = float(profile.total_donated or 0) + 5000
    ngo.net_funding = float(ngo.net_funding or 0) + 5000

    db.commit()
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
