import sys
import os
import uuid
import bcrypt
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to sys.path so app module can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.database import Base, engine, SessionLocal
from app.models import User, UserRole, DonatorProfile, NGOPersonnel, NGO, StudentProfile

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_db():
    print("Starting DB Seed for Simulation...")
    db = SessionLocal()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Check if already seeded
    existing_user = db.query(User).filter_by(email="donor@example.com").first()
    if existing_user:
        print("DB already seeded with default test users! Exiting.")
        return

    # Seed NGOs
    ngo1 = NGO(
        name="EduCare India",
        description="Providing education to rural students. Our mission is to bridge the educational gap.",
        bank_account_number="ACC123456789",
        bank_ifsc_code="HDFC0001234",
        upi_id="educare@icici",
        blockchain_uid=101,
        net_funding=0.0
    )
    
    ngo2 = NGO(
        name="Rural Scholars Foundation",
        description="Empowering scholars from rural backgrounds with the tools they need to succeed.",
        bank_account_number="ACC987654321",
        bank_ifsc_code="SBIN0005678",
        upi_id="ruralscholars@sbi",
        blockchain_uid=102,
        net_funding=0.0
    )
    db.add_all([ngo1, ngo2])
    db.commit()
    
    # Seed Donor User
    donor_user = User(
        email="donor@example.com",
        password=get_password_hash("password123"),
        full_name="Alice Donor",
        role=UserRole.DONATOR,
        blockchain_uid=201
    )
    db.add(donor_user)
    db.commit()
    
    donor_profile = DonatorProfile(
        user_id=donor_user.id,
        has_donated=False,
        total_donated=0.0
    )
    db.add(donor_profile)
    
    # Seed NGO Personnel User
    ngo_user = User(
        email="ngo@example.com",
        password=get_password_hash("password123"),
        full_name="Bob NGO Manager",
        role=UserRole.NGO_PERSONNEL,
        blockchain_uid=301
    )
    db.add(ngo_user)
    db.commit()
    
    ngo_personnel = NGOPersonnel(
        user_id=ngo_user.id,
        ngo_id=ngo1.id,
        designation="Director"
    )
    db.add(ngo_personnel)
    
    # Seed Student User
    student_user = User(
        email="student@example.com",
        password=get_password_hash("password123"),
        full_name="Charlie Student",
        role=UserRole.STUDENT,
        blockchain_uid=401
    )
    db.add(student_user)
    db.commit()
    
    student_profile = StudentProfile(
        user_id=student_user.id,
        institution_name="Delhi University",
        course="B.Tech Computer Science",
        annual_family_income=250000.0,
        bank_account_number="2233445566",
        bank_ifsc_code="SBIN0001234"
    )
    db.add(student_profile)
    
    db.commit()
    print("DB Seeding Complete!")
    print("Credentials Created:")
    print(" DONOR: donor@example.com / password123")
    print(" NGO:   ngo@example.com / password123")
    print(" STUDENT: student@example.com / password123")
    
if __name__ == "__main__":
    seed_db()
