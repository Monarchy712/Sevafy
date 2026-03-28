from app.database import SessionLocal
from app import models
import json

def dump():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        ngos = db.query(models.NGO).all()
        personnel = db.query(models.NGOPersonnel).all()
        
        print("USERS:")
        for u in users:
            print(f"- {u.email} (Role: {u.role}, UID: {u.blockchain_uid})")
            
        print("\nNGOS:")
        for n in ngos:
            print(f"- {n.name} (UID: {n.blockchain_uid})")
            
        print("\nPERSONNEL LINK:")
        for p in personnel:
            user = db.query(models.User).filter(models.User.id == p.user_id).first()
            ngo = db.query(models.NGO).filter(models.NGO.id == p.ngo_id).first()
            print(f"- {user.email if user else 'Unknown'} -> {ngo.name if ngo else 'Unknown'}")
            
    finally:
        db.close()

if __name__ == "__main__":
    dump()
