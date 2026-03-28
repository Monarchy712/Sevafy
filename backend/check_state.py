import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.append(os.getcwd())

from app import models
from app.database import SessionLocal, engine

def check():
    db = SessionLocal()
    try:
        # Check NGOs
        ngos = db.query(models.NGO).all()
        print(f"Total NGOs: {len(ngos)}")
        for n in ngos:
            print(f" NGO: {n.name}, UID: {n.blockchain_uid}, ID: {n.id}")

        # Check Users
        users = db.query(models.User).filter(models.User.role == "NGO_PERSONNEL").all()
        print(f"\nNGO Personnel Users: {len(users)}")
        for u in users:
            print(f" User: {u.email}, UID: {u.blockchain_uid}, ID: {u.id}")

        # Check Personnel Table
        links = db.query(models.NGOPersonnel).all()
        print(f"\nPersonnel Links: {len(links)}")
        for l in links:
            print(f" Link: User_ID {l.user_id} -> NGO_ID {l.ngo_id}")

        # Check Blockchain Config
        from app import blockchain
        try:
            w3 = blockchain._get_web3()
            connected = w3.is_connected()
            print(f"\nBlockchain Connected: {connected}")
            if connected:
                print(f" Block Number: {w3.eth.block_number}")
        except Exception as e:
            print(f"\nBlockchain Error: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    check()
