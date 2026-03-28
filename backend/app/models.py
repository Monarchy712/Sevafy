import uuid
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from .database import Base

class UserRole(str, enum.Enum):
    DONATOR = "DONATOR"
    STUDENT = "STUDENT"
    NGO_PERSONNEL = "NGO_PERSONNEL"

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
    
    # Encrypted fields handling omitted for MVP simplicity, saving as text 
    # (can add pgcrypto handling later, but we keep it functionally identical for now)
    bank_account_number = Column(Text, nullable=True)
    bank_ifsc_code = Column(Text, nullable=True)
    wallet_address = Column(String(66), nullable=True)

    user = relationship("User", back_populates="student_profile")

class DonatorProfile(Base):
    __tablename__ = "donator_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    pan_number = Column(Text, nullable=True)
    bank_account_number = Column(Text, nullable=True)
    bank_ifsc_code = Column(Text, nullable=True)

    user = relationship("User", back_populates="donator_profile")

# For MVP, we'll keep these other tables as placeholders to finish later
# but these user & roles are the backbone for Authentication right now.
