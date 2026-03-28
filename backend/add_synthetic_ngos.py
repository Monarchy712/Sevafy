import sys
import os
import random

sys.path.append(os.path.abspath('c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend'))
from app.database import SessionLocal, engine
from sqlalchemy import text
from app import models

def run():
    # Add logo_url column
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE ngos ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500);"))
        conn.commit()

    db = SessionLocal()
    
    # 1. Update existing NGOs
    existing = db.query(models.NGO).all()
    for idx, e in enumerate(existing):
        e.logo_url = f"https://picsum.photos/400/250?random={random.randint(100, 999)}"
    
    # 2. Add 5 synthetic NGOs
    names = [
        "TechForGood Foundation", 
        "Global Clean Water Org", 
        "Animal Rescue Network", 
        "Solar Pioneers India", 
        "Women in Tech Initiative"
    ]
    descriptions = [
        "Providing laptops and internet access to underprivileged communities.",
        "Building wells and water purifiers in remote villages.",
        "Rescuing and rehabilitating abandoned pets and street animals.",
        "Installing solar panels in schools to provide continuous electricity.",
        "Running bootcamps to teach coding and technical skills to young girls."
    ]
    
    for i in range(5):
        new_ngo = models.NGO(
            name=names[i],
            description=descriptions[i],
            about=f"Our mission is to lead efforts in the {names[i]} initiatives everywhere.",
            net_funding=0.0,
            beneficiary=["General Public", "Students"],
            logo_url=f"https://picsum.photos/400/250?random={random.randint(1000, 9999)}",
            bank_account_number=f"SYNTH{i}000001",
            bank_ifsc_code=f"SYNTH{i}000",
            upi_id=f"synth_{i}@upi",
            blockchain_uid=500 + i
        )
        db.add(new_ngo)

    db.commit()
    print(f"Successfully updated {len(existing)} existing NGOs and added 5 new synthetic NGOs.")

if __name__ == '__main__':
    run()
