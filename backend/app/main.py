from fastapi import FastAPI, Depends, HTTPException, status
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

from . import models, schemas, auth
from .database import engine, get_db
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from .ml_service import get_top_ngos

# Google Client ID from environment
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]

# Create all database tables based on our models
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sevafy API")

# Update CORS to allow requests from the React frontend running on localhost:5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Fine for MVP, but should lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Sevafy API"}

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    # Create the user object
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize associated profile depending on the role
    if user.role == models.UserRole.STUDENT:
        new_profile = models.StudentProfile(user_id=new_user.id)
        db.add(new_profile)
    elif user.role == models.UserRole.DONATOR:
        new_profile = models.DonatorProfile(user_id=new_user.id)
        db.add(new_profile)
        
    db.commit()
    
    # We must format to our response model
    return schemas.UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role
    )

@app.post("/api/auth/login", response_model=schemas.Token)
def login_for_access_token(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not auth.verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/google")
def google_auth(request: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        # Verify the ID token using the official Google library
        id_info = id_token.verify_oauth2_token(request.credential, requests.Request(), GOOGLE_CLIENT_ID)
        
        email = id_info['email']
        google_id = id_info['sub']
        full_name = id_info.get('name', 'Google User')
        
        # Check if user exists by email or google_id
        user = db.query(models.User).filter(
            (models.User.email == email) | (models.User.google_id == google_id)
        ).first()
        
        if user:
            # Sync google_id if it somehow wasn't set but email matches
            if not user.google_id:
                user.google_id = google_id
                db.commit()
                
            access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = auth.create_access_token(
                data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer", "require_role": False}
        else:
            # Signal the frontend to ask for a role
            return {
                "require_role": True, 
                "email": email, 
                "full_name": full_name, 
                "google_id": google_id
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

@app.post("/api/auth/google/complete")
def google_complete(request: schemas.GoogleCompleteRequest, db: Session = Depends(get_db)):
    # Verify user doesn't exist yet before final creation
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists with this email")

    # Create the user without a password (Google logins)
    new_user = models.User(
        email=request.email,
        full_name=request.full_name,
        google_id=request.google_id,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize associated profile depending on role
    if request.role == models.UserRole.STUDENT:
        db.add(models.StudentProfile(user_id=new_user.id))
    elif request.role == models.UserRole.DONATOR:
        db.add(models.DonatorProfile(user_id=new_user.id))
        
    db.commit()
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": new_user.email, "role": new_user.role.value}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

import requests as external_requests

@app.post("/api/auth/google/custom")
def google_custom_auth(request: schemas.GoogleCustomRequest, db: Session = Depends(get_db)):
    # Verify access_token by calling Google's UserInfo API
    resp = external_requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {request.access_token}"}
    )
    
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google access token")
    
    user_info = resp.json()
    email = user_info['email']
    google_id = user_info['sub']
    full_name = user_info.get('name', 'Google User')
    
    # Same logic as standard google login
    user = db.query(models.User).filter(
        (models.User.email == email) | (models.User.google_id == google_id)
    ).first()
    
    if user:
        if not user.google_id:
            user.google_id = google_id
            db.commit()
            
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = auth.create_access_token(
            data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
        )
        return {"access_token": jwt_token, "token_type": "bearer", "require_role": False}
    else:
        return {
            "require_role": True, 
            "email": email, 
            "full_name": full_name, 
            "google_id": google_id
        }

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return schemas.UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role
    )

@app.get("/api/ngos/recommendations", response_model=List[schemas.NGORecommendation])
def get_ngo_recommendations(db: Session = Depends(get_db)):
    """
    Returns the top 5 NGOS optimized for fair funding distribution and highest student impact.
    Powered by the XGBoost ML model.
    """
    all_ngos = db.query(models.NGO).all()
    
    if not all_ngos:
        return []
    
    top_5 = get_top_ngos(db, all_ngos)
    
    response = []
    for item in top_5:
        ngo_out = schemas.NGOOut(
            id=str(item["ngo"].id),
            name=item["ngo"].name,
            description=item["ngo"].description
        )
        response.append(
            schemas.NGORecommendation(
                ngo=ngo_out,
                impact_score=item["impact_score"],
                rank=item["rank"],
                features=item["features"]
            )
        )
    return response

# ── NGO & Donor Endpoints ─────────────────────────────

from typing import List
import uuid as uuid_module

@app.get("/api/ngos", response_model=List[schemas.NGOResponse])
def list_ngos(db: Session = Depends(get_db)):
    """Public endpoint: returns all partner NGOs."""
    ngos = db.query(models.NGO).all()
    return [
        schemas.NGOResponse(
            id=str(n.id),
            name=n.name,
            description=n.description,
            about=n.about,
            net_funding=float(n.net_funding or 0),
            beneficiary=n.beneficiary or []
        )
        for n in ngos
    ]

@app.post("/api/donate")
def donate(
    request: schemas.DonateRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a donation. Flips has_donated and increments total_donated."""
    if current_user.role != models.UserRole.DONATOR:
        raise HTTPException(status_code=403, detail="Only donators can donate")
    
    profile = db.query(models.DonatorProfile).filter(
        models.DonatorProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Donator profile not found")
    
    # Update donor profile
    profile.has_donated = True
    profile.total_donated = float(profile.total_donated or 0) + request.amount
    
    # Update NGO net funding
    ngo = db.query(models.NGO).filter(
        models.NGO.id == uuid_module.UUID(request.ngo_id)
    ).first()
    if ngo:
        ngo.net_funding = float(ngo.net_funding or 0) + request.amount
    
    db.commit()
    return {"status": "success", "total_donated": float(profile.total_donated)}

@app.get("/api/donor/status", response_model=schemas.DonorStatusResponse)
def donor_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the donor's has_donated flag and total_donated amount."""
    if current_user.role != models.UserRole.DONATOR:
        raise HTTPException(status_code=403, detail="Not a donator")
    
    profile = db.query(models.DonatorProfile).filter(
        models.DonatorProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Donator profile not found")
    
    return schemas.DonorStatusResponse(
        has_donated=profile.has_donated,
        total_donated=float(profile.total_donated or 0)
    )
