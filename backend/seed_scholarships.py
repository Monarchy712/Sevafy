import uuid
from app.database import SessionLocal
from app.models import ScholarshipScheme, NGO

def seed_scholarships():
    db = SessionLocal()
    try:
        # Get first NGO
        ngo = db.query(NGO).first()
        if not ngo:
            print("No NGOs found. Please seed NGOs first.")
            return

        # Check if scholarships already exist
        if db.query(ScholarshipScheme).count() > 0:
            print("Scholarships already seeded.")
            return

        example_schemes = [
            {
                "title": "Rural Merit 2026",
                "description": "Funding for top-performing students from rural districts of India.",
                "amount_per_student": 75000.00,
                "ngo_id": ngo.id
            },
            {
                "title": "STEM Village Grant",
                "description": "Special grant for science and engineering students in village communities.",
                "amount_per_student": 50000.00,
                "ngo_id": ngo.id
            },
            {
                "title": "Leader Award",
                "description": "Merit-based scholarship for high school leaders aiming for higher education.",
                "amount_per_student": 25000.00,
                "ngo_id": ngo.id
            }
        ]

        for s in example_schemes:
            new_scheme = ScholarshipScheme(**s)
            db.add(new_scheme)
        
        db.commit()
        print(f"Successfully seeded {len(example_schemes)} scholarship schemes.")
    except Exception as e:
        print(f"Error seeding scholarships: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_scholarships()
