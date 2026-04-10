import os
import sys
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from uuid import uuid4

# Setup path
sys.path.append(os.getcwd())

from app import models
from app.database import SessionLocal

def populate_scholarships():
    db = SessionLocal()
    try:
        # 1. Clear existing scholarships
        print("Clearing existing scholarships...")
        db.query(models.ScholarshipScheme).delete()
        db.commit()

        # 2. Fetch all NGOs
        ngos = db.query(models.NGO).all()
        if not ngos:
            print("No NGOs found. Seed NGOs first.")
            return

        print(f"Found {len(ngos)} NGOs.")

        # 3. Create synthetic scholarships
        scholarship_data = [
            ("STEM Excellence Grant", "Support for exceptional science students."),
            ("Village Bright Sparks", "Helping rural kids reach their potential."),
            ("Undergraduate Catalyst", "Fueling higher education dreams."),
            ("High School Hero Scholarship", "Rewarding leadership in schools."),
            ("Primary Pathways Fund", "Getting the basics right for every child."),
            ("Future Leaders Award", "Empowering the next generation of changemakers."),
            ("Technical Bridge Grant", "Transitioning from school to tech careers."),
            ("Regional Merit Scholarship", "Top scorers from underserved districts."),
            ("Women in Science Grant", "Encouraging female students in STEM fields."),
            ("Digital Literacy Award", "Providing tech access for rural learners."),
            ("Community Impact Grant", "For students leading local social projects."),
            ("Academic Renewal Fund", "Annual support for continuing students."),
            ("Emerging Scholar Award", "Recognizing untapped potential in mid-school.")
        ]

        print(f"Creating {len(scholarship_data)} scholarships...")

        for title, desc in scholarship_data:
            ngo = random.choice(ngos)
            
            # Pick a beneficiary from the NGO's list
            # NGO.beneficiary is often a list/array
            beneficiary_options = ngo.beneficiary if ngo.beneficiary else ["undergrad"]
            beneficiary = random.choice(beneficiary_options)

            # Random amount between 10k and 150k
            amount = random.randint(100, 1500) * 100 

            # Random deadline within 3 weeks (1 to 21 days)
            days_to_deadline = random.randint(1, 21)
            deadline = datetime.now(timezone.utc) + timedelta(days=days_to_deadline)

            new_scheme = models.ScholarshipScheme(
                id=uuid4(),
                ngo_id=ngo.id,
                title=title,
                description=desc,
                amount_per_student=amount,
                scheme_beneficiary=beneficiary,
                deadline=deadline
            )
            db.add(new_scheme)
            print(f" [ADDED] {title} (NGO: {ngo.name}, Beneficiary: {beneficiary}, Deadline: {deadline.strftime('%Y-%m-%d')})")

        db.commit()
        print("\nScholarship population complete!")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    populate_scholarships()
