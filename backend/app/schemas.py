from pydantic import BaseModel, EmailStr
from typing import Optional
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

# New Google Auth Schemas
class GoogleAuthRequest(BaseModel):
    credential: str

class GoogleCompleteRequest(BaseModel):
    email: EmailStr
    full_name: str
    google_id: str
    role: UserRole

class GoogleCustomRequest(BaseModel):
    access_token: str

class NGOOut(BaseModel):
    id: str  # Send UUID as string
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class NGORecommendation(BaseModel):
    ngo: NGOOut
    impact_score: float
    rank: int
    features: dict
