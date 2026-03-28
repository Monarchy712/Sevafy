from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .models import UserRole

# ── Auth Schemas ──────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str  # Send UUID as string
    email: str
    full_name: str
    role: UserRole
    blockchain_uid: int  # Stable blockchain UID — assigned once at user creation, never changes

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ── Google Auth Schemas ───────────────────────────────────

class GoogleAuthRequest(BaseModel):
    credential: str

class GoogleCompleteRequest(BaseModel):
    email: EmailStr
    full_name: str
    google_id: str
    role: UserRole

class GoogleCustomRequest(BaseModel):
    access_token: str

# ── NGO Schemas ───────────────────────────────────────────

class NGOOut(BaseModel):
    id: str  # Send UUID as string
    name: str
    description: Optional[str] = None
    blockchain_uid: int  # Stable blockchain UID for contract mapping

    class Config:
        orm_mode = True

class NGOResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    about: Optional[str] = None
    net_funding: float = 0
    beneficiary: Optional[List[str]] = None
    logo_url: Optional[str] = None
    blockchain_uid: int  # Stable blockchain UID for contract mapping

    class Config:
        orm_mode = True

class NGORecommendation(BaseModel):
    ngo: NGOOut
    impact_score: float
    rank: int
    features: dict

# ── Donate Schemas ────────────────────────────────────────

class DonateRequest(BaseModel):
    ngo_id: str
    amount: float

class DonateResponse(BaseModel):
    status: str
    total_donated: float
    donation_id: Optional[str] = None  # DB donationId (UUID)
    tx_hash: Optional[str] = None
    confirmed: bool = False

# ── Donor Status ──────────────────────────────────────────

class DonorStatusResponse(BaseModel):
    has_donated: bool
    total_donated: float

    class Config:
        orm_mode = True

# ── Blockchain Transaction Record ─────────────────────────

class TransactionRecord(BaseModel):
    """Unified transaction record from the database."""
    purpose: Optional[int] = None
    donation_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: str  # ISO formatted string
    tx_type: str  # "DONOR_TO_NGO" or "NGO_TO_STUDENT"

class RemainingFundsResponse(BaseModel):
    donation_id: str
    remaining_funds: float
    fully_used: bool

class StudentFundedRecord(BaseModel):
    purpose: int
    donation_id: str
    ngo_id: str
    student_id: str
    amount: float
    timestamp: str

class LedgerResponse(BaseModel):
    transactions: List[TransactionRecord]
    count: int

# ── Fund Transfer (NGO → Student) ────────────────────────

class FundTransferRequest(BaseModel):
    application_id: str  # UUID of the ScholarshipApplication
    donation_id: str     # DB donationId to draw from
    amount: float
    purpose: int         # InstallmentPhase as int

class FundTransferResponse(BaseModel):
    status: str
    tx_hash: Optional[str] = None
    donation_id: str
    remaining_funds: Optional[float] = None
    verification_result: Optional[dict] = None

# ── Student Verification ──────────────────────────────────

class VerifyAndTransferRequest(BaseModel):
    application_id: str  # UUID of ScholarshipApplication
    donation_id: str     # DB donationId
    amount: float
    purpose: int         # InstallmentPhase as int
    documents: List[dict]  # [{"type": "...", "description": "..."}]

class VerificationResponse(BaseModel):
    valid: bool
    reason: str
    confidence: float
    details: Optional[dict] = None

# ── NGO Approval ──────────────────────────────────────────

class ApproveStudentRequest(BaseModel):
    application_id: str  # UUID of ScholarshipApplication

class ApproveStudentResponse(BaseModel):
    status: str
    application_id: str
    new_status: str
