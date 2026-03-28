import uuid
import random
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def seed_data():
    db = SessionLocal()
    try:
        # 1. Create 10 NGOs with different profiles
        ngo_profiles = [
            {"name": "Lotus Foundation", "desc": "Focus on extreme poverty in rural areas.", "income": 12000, "funding": 0.1, "backlog": 45},
            {"name": "Bright Future Scholars", "desc": "Supporting higher education for urban youth.", "income": 85000, "funding": 0.8, "backlog": 10},
            {"name": "Tech for All", "desc": "Providing devices and coding skills.", "income": 50000, "funding": 0.4, "backlog": 25},
            {"name": "Green Earth Education", "desc": "Environmental science scholarships.", "income": 40000, "funding": 0.6, "backlog": 15},
            {"name": "Women in STEM", "desc": "Empowering young women in engineering.", "income": 30000, "funding": 0.2, "backlog": 35},
            {"name": "Rural Reach", "desc": "Supporting basic literacy in remote villages.", "income": 15000, "funding": 0.05, "backlog": 60},
            {"name": "Urban Uplift", "desc": "Vocational training for city dropouts.", "income": 60000, "funding": 0.7, "backlog": 12},
            {"name": "Healthcare Heroes", "desc": "Scholarships for nursing students.", "income": 45000, "funding": 0.3, "backlog": 28},
            {"name": "Artistic Souls", "desc": "Supporting traditional arts and crafts.", "income": 25000, "funding": 0.9, "backlog": 5},
            {"name": "Infinite Potential", "desc": "General purpose education support.", "income": 35000, "funding": 0.5, "backlog": 20},
        ]

        for profile in ngo_profiles:
            # Create NGO
            ngo = models.NGO(
                name=profile["name"],
                description=profile["desc"],
                bank_account_number="1234567890",
                bank_ifsc_code="SBIN0001234",
                upi_id=f"{profile['name'].lower().replace(' ', '')}@upi"
            )
            db.add(ngo)
            db.flush()

            # Create some Schemes for this NGO
            scheme = models.ScholarshipScheme(
                ngo_id=ngo.id,
                title=f"{profile['name']} General Scholarship",
                description=f"Standard support scheme from {profile['name']}.",
                amount_per_student=5000.00
            )
            db.add(scheme)
            db.flush()

            # Seed some fake metrics indirectly (by creating applications and donations)
            # To simulate low funding, we create few donations.
            # To simulate backlog, we create many approved apps.
            
            # 1. Create Donations (based on profile['funding'])
            # (Roughly, we'll just add some donation records)
            donor_user = db.query(models.User).filter(models.User.role == models.UserRole.DONATOR).first()
            if not donor_user:
                # Create a mock donor if none exists
                donor_user = models.User(
                    email=f"donor_{uuid.uuid4().hex[:4]}@example.com",
                    full_name="Seed Donor",
                    role=models.UserRole.DONATOR
                )
                db.add(donor_user)
                db.flush()
                donor_profile = models.DonatorProfile(user_id=donor_user.id)
                db.add(donor_profile)
                db.flush()
            else:
                donor_profile = donor_user.donator_profile

            # Add donations based on funding percentage relative to a target
            target_amount = 100000
            actual_donation = target_amount * profile["funding"]
            donation = models.Donation(
                donator_id=donor_profile.id,
                ngo_id=ngo.id,
                amount=actual_donation
            )
            db.add(donation)

            # 2. Create Applications (based on profile['backlog'] and profile['income'])
            for i in range(profile["backlog"]):
                # Create a mock student
                student_user = models.User(
                    email=f"student_{ngo.name[:3]}_{i}@example.com",
                    full_name=f"Student {i}",
                    role=models.UserRole.STUDENT
                )
                db.add(student_user)
                db.flush()
                student_profile = models.StudentProfile(
                    user_id=student_user.id,
                    annual_family_income=profile["income"] + random.randint(-5000, 5000)
                )
                db.add(student_profile)
                db.flush()

                # Apply and Approve
                app = models.ScholarshipApplication(
                    scheme_id=scheme.id,
                    student_id=student_profile.id,
                    status=models.ApplicationStatus.APPROVED
                )
                db.add(app)
        
        db.commit()
        print("✅ Database successfully seeded with 10 NGOs and real-world metrics!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
