import uuid
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .database import Base

class UserRole(str, enum.Enum):
    DONATOR = "DONATOR"
    STUDENT = "STUDENT"
    NGO_PERSONNEL = "NGO_PERSONNEL"

class ApplicationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class InstallmentPhase(int, enum.Enum):
    NEW_ADMISSION = 0
    MID_TERM_INSTALLMENT = 1

class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(Text, nullable=True) # Nullable for Google-only users
    full_name = Column(String(255), nullable=False)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    role = Column(SQLEnum(UserRole), nullable=False)
    wallet_address = Column(String(66), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    donator_profile = relationship("DonatorProfile", back_populates="user", uselist=False)

class NGO(Base):
    __tablename__ = "ngos"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    about = Column(Text, nullable=True)  # Vision/mission statement
    net_funding = Column(Numeric(14, 2), nullable=False, default=0)  # Total funding received
    beneficiary = Column(ARRAY(Text), nullable=True)  # e.g. ["elementary", "undergrad"]
    bank_account_number = Column(String(30), nullable=False)
    bank_ifsc_code = Column(String(11), nullable=False)
    upi_id = Column(String(100), nullable=False)
    wallet_address = Column(String(66), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    institution_name = Column(String(255), nullable=True)
    course = Column(String(255), nullable=True)
    annual_family_income = Column(Numeric(14, 2), nullable=True)
    
    bank_account_number = Column(Text, nullable=True)
    bank_ifsc_code = Column(Text, nullable=True)
    wallet_address = Column(String(66), nullable=True)

    user = relationship("User", back_populates="student_profile")

class DonatorProfile(Base):
    __tablename__ = "donator_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    has_donated = Column(Boolean, nullable=False, default=False)  # Controls overlay
    total_donated = Column(Numeric(14, 2), nullable=False, default=0)  # Running total
    pan_number = Column(Text, nullable=True)
    bank_account_number = Column(Text, nullable=True)
    bank_ifsc_code = Column(Text, nullable=True)

    user = relationship("User", back_populates="donator_profile")

# For MVP, we'll keep these other tables as placeholders to finish later
# but these user & roles are the backbone for Authentication right now.

class ScholarshipScheme(Base):
    __tablename__ = "scholarship_schemes"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ngo_id = Column(PG_UUID(as_uuid=True), ForeignKey("ngos.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    amount_per_student = Column(Numeric(14, 2), nullable=False)
    contract_address = Column(String(66), nullable=True)

class ScholarshipApplication(Base):
    __tablename__ = "scholarship_applications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = Column(PG_UUID(as_uuid=True), ForeignKey("scholarship_schemes.id"), nullable=False)
    student_id = Column(PG_UUID(as_uuid=True), ForeignKey("student_profiles.id"), nullable=False)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.SUBMITTED)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

class ScholarshipInstallment(Base):
    __tablename__ = "scholarship_installments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(PG_UUID(as_uuid=True), ForeignKey("scholarship_applications.id"), nullable=False)
    phase = Column(SQLEnum(InstallmentPhase), nullable=False)
    amount = Column(Numeric(14,2), nullable=False)
    is_disbursed = Column(Boolean, default=False)
    tx_hash = Column(String(130), nullable=True)
    disbursed_at = Column(DateTime(timezone=True), nullable=True)

class Donation(Base):
    __tablename__ = "donations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donator_id = Column(PG_UUID(as_uuid=True), ForeignKey("donator_profiles.id"), nullable=False)
    ngo_id = Column(PG_UUID(as_uuid=True), ForeignKey("ngos.id"), nullable=False)
    amount = Column(Numeric(16,2), nullable=False)
    tx_hash = Column(String(130), nullable=True)
    donated_at = Column(DateTime(timezone=True), server_default=func.now())
