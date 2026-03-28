import traceback
import sys
import os

sys.path.append(os.path.abspath('c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend'))
from app.database import SessionLocal
from app import models, blockchain

db = SessionLocal()
donor = db.query(models.User).filter_by(role=models.UserRole.DONATOR).first()
ngo = db.query(models.NGO).first()

try:
    print(f"Calling donorPaymentCall with donor={donor.blockchain_uid}, ngo={ngo.blockchain_uid}, amount=500")
    res = blockchain.call_donor_payment(donor.blockchain_uid, ngo.blockchain_uid, 500)
    print("Success:", res)
except Exception as e:
    traceback.print_exc()
