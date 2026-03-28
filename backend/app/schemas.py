from pydantic import BaseModel, EmailStr
from typing import Optional, List
from .models import UserRole

# Basic Schemas for Auth
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

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Google Auth Schemas
class GoogleAuthRequest(BaseModel):
    credential: str

class GoogleCompleteRequest(BaseModel):
    email: EmailStr
    full_name: str
    google_id: str
    role: UserRole

class GoogleCustomRequest(BaseModel):
    access_token: str

# NGO Schemas
class NGOResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    about: Optional[str] = None
    net_funding: float = 0
    beneficiary: Optional[List[str]] = None

    class Config:
        orm_mode = True

# Donate Schema
class DonateRequest(BaseModel):
    ngo_id: str
    amount: float

# Donor Status
class DonorStatusResponse(BaseModel):
    has_donated: bool
    total_donated: float

    class Config:
        orm_mode = True
