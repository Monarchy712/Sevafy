import os, sys
sys.path.append(os.getcwd())
from dotenv import load_dotenv
load_dotenv()

from app import models
from app.database import SessionLocal

db = SessionLocal()

# Check all NGO personnel users and their links
print("=== NGO Personnel Users ===")
users = db.query(models.User).filter(models.User.role == models.UserRole.NGO_PERSONNEL).all()
for u in users:
    link = db.query(models.NGOPersonnel).filter(models.NGOPersonnel.user_id == u.id).first()
    ngo = db.query(models.NGO).filter(models.NGO.id == link.ngo_id).first() if link else None
    print(f"  {u.email} -> Link: {'YES' if link else 'NO'} -> NGO: {ngo.name if ngo else 'NONE'}")

print("\n=== All NGOs ===")
ngos = db.query(models.NGO).all()
for n in ngos:
    print(f"  {n.name} (id={n.id}, uid={n.blockchain_uid})")

db.close()
