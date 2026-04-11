from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
import asyncio
import uuid

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

from . import models, schemas, auth
from .database import engine, get_db, SessionLocal
from google.oauth2 import id_token
from google.auth.transport import requests
from .ml_service import get_top_ngos

# Blockchain aur websocket ke liye zaroori imports
from . import blockchain
from .genai_verifier import verify_student_documents
from .websocket_manager import ws_manager
from .event_listener import start_event_listener
from .ngo_router import router as ngo_router

# Google OAuth ke liye Client ID uthao
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# Database tables banao agar nahi hai toh
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sevafy API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ngo_router, prefix="/api")


# ── Startup: launch event listener ────────────────────────


@app.on_event("startup")
async def startup_event():
    # Blockchain listener ko background mein chalao simulation mode ke liye
    try:
        # asyncio.create_task(start_event_listener(SessionLocal, ws_manager))
        import logging
        logging.getLogger(__name__).info("Blockchain event listener disabled for simulation mode.")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Event listener failed to start: %s", e)




# We'll replace this with static file serving at the bottom for better catch-all handling.
# @app.get("/")
# def read_root():
#     return {"message": "Welcome to Sevafy API"}


@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # User add hogaya, ab role ke hisab se profile banao
    if user.role == models.UserRole.STUDENT:
        new_profile = models.StudentProfile(user_id=new_user.id)
        db.add(new_profile)
    elif user.role == models.UserRole.DONATOR:
        new_profile = models.DonatorProfile(user_id=new_user.id)
        db.add(new_profile)

    db.commit()

    return schemas.UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        blockchain_uid=new_user.blockchain_uid
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
    # Google token verify karo, fir check karo user exist karta hai ya nahi
    try:
        id_info = id_token.verify_oauth2_token(request.credential, requests.Request(), GOOGLE_CLIENT_ID)

        email = id_info['email']
        google_id = id_info['sub']
        full_name = id_info.get('name', 'Google User')

        user = db.query(models.User).filter(
            (models.User.email == email) | (models.User.google_id == google_id)
        ).first()

        if user:
            if not user.google_id:
                user.google_id = google_id
                db.commit()

            access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = auth.create_access_token(
                data={"sub": user.email, "role": user.role.value}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer", "require_role": False}
        else:
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
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists with this email")

    new_user = models.User(
        email=request.email,
        full_name=request.full_name,
        google_id=request.google_id,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

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
        role=current_user.role,
        blockchain_uid=current_user.blockchain_uid,
    )




@app.get("/api/ngos/recommendations", response_model=List[schemas.NGORecommendation])
def get_ngo_recommendations(db: Session = Depends(get_db)):
    """Returns the top 5 NGOs optimized for fair funding distribution and highest student impact."""
    all_ngos = db.query(models.NGO).all()
    if not all_ngos:
        return []

    top_5 = get_top_ngos(db, all_ngos)

    response = []
    for item in top_5:
        ngo_out = schemas.NGOOut(
            id=str(item["ngo"].id),
            name=item["ngo"].name,
            description=item["ngo"].description,
            blockchain_uid=item["ngo"].blockchain_uid
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
            beneficiary=n.beneficiary or [],
            blockchain_uid=n.blockchain_uid
        )
        for n in ngos
    ]




@app.post("/api/donate", response_model=schemas.DonateResponse)
def donate(
    request: schemas.DonateRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != models.UserRole.DONATOR:
        raise HTTPException(status_code=403, detail="Only donators can donate")

    profile = db.query(models.DonatorProfile).filter(
        models.DonatorProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Donator profile not found")

    ngo = db.query(models.NGO).filter(
        models.NGO.id == uuid_module.UUID(request.ngo_id)
    ).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")

    # Donation amount uint mein convert karke contract call karo
    from app import blockchain
    try:
        bc_res = blockchain.call_donor_payment(
            donor_uid=current_user.blockchain_uid,
            ngo_uid=ngo.blockchain_uid,
            amount=int(request.amount)
        )
        tx_hash = bc_res.get("tx_hash", "SIMULATED_SUCCESS")
        bc_donation_id = bc_res.get("donation_id")
    except Exception as e:
        print("Blockchain Error:", e)
        raise HTTPException(status_code=500, detail=f"Blockchain transaction failed: {str(e)}")

    donation = models.Donation(
        donator_id=profile.id,
        ngo_id=ngo.id,
        amount=request.amount,
        remaining_amount=request.amount,
        confirmed=True,
        tx_hash=tx_hash,
        blockchain_donation_id=bc_donation_id
    )
    db.add(donation)
    
    profile.has_donated = True
    profile.total_donated = float(profile.total_donated or 0) + request.amount
    ngo.net_funding = float(ngo.net_funding or 0) + request.amount

    db.commit()
    db.refresh(donation)
    db.refresh(profile)

    return schemas.DonateResponse(
        status="success",
        total_donated=float(profile.total_donated),
        donation_id=str(bc_donation_id) if bc_donation_id is not None else str(donation.id),
        tx_hash=tx_hash,
        confirmed=True,
    )


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


@app.get("/api/simulate-scan/{ngo_id}/{amount}/{user_id}")
async def simulate_scan(ngo_id: str, amount: float, user_id: str):
    """
    Simulates a phone scanning the donation QR code.
    Sends a message to the desktop client via WebSocket to trigger auto-completion.
    """
    await ws_manager.broadcast_to_donor(user_id, {
        "type": "payment_scanned",
        "ngo_id": ngo_id,
        "amount": amount
    })
    return {"status": "success", "message": "Payment signal sent to desktop dashboard"}


# ══════════════════════════════════════════════════════════
# NGO APPROVAL ENDPOINT (DB only — NO blockchain)
# ══════════════════════════════════════════════════════════


@app.post("/api/ngo/approve-student", response_model=schemas.ApproveStudentResponse)
def approve_student(
    request: schemas.ApproveStudentRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Sirf DB update karo, blockchain call transfer endpoint pe hoga
    if current_user.role != models.UserRole.NGO_PERSONNEL:
        raise HTTPException(status_code=403, detail="Only NGO personnel can approve students")

    application = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.id == uuid_module.UUID(request.application_id)
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != models.ApplicationStatus.SUBMITTED:
        raise HTTPException(
            status_code=400,
            detail=f"Application cannot be approved — current status: {application.status.value}"
        )

    application.status = models.ApplicationStatus.APPROVED
    db.commit()

    return schemas.ApproveStudentResponse(
        status="success",
        application_id=str(application.id),
        new_status=application.status.value,
    )



@app.post("/api/student/verify-and-transfer", response_model=schemas.FundTransferResponse)
def verify_and_transfer(
    request: schemas.VerifyAndTransferRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != models.UserRole.NGO_PERSONNEL:
        raise HTTPException(status_code=403, detail="Only NGO personnel can trigger fund transfers")

    application = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.id == uuid_module.UUID(request.application_id)
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status != models.ApplicationStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Application must be APPROVED before fund transfer. Current: {application.status.value}"
        )
        
    donation = db.query(models.Donation).filter(
        models.Donation.id == uuid_module.UUID(request.donation_id)
    ).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation record not found")
        
    if float(request.amount) > float(donation.remaining_amount):
        raise HTTPException(
            status_code=400, 
            detail=f"Transfer amount ({request.amount}) exceeds remaining donation amount ({donation.remaining_amount})"
        )

    # Get student info
    student_profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.id == application.student_id
    ).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    student_user = db.query(models.User).filter(
        models.User.id == student_profile.user_id
    ).first()

    # GenAI verification (Mocked)
    verification = verify_student_documents(
        student_name=student_user.full_name,
        institution_name=student_profile.institution_name or "",
        course=student_profile.course or "",
        annual_income=float(student_profile.annual_family_income or 0),
        documents=request.documents,
    )

    # GenAI ka result save karo aur DB check karo
    application.verified_by_genai = verification.valid
    application.genai_result = {
        "valid": verification.valid,
        "reason": verification.reason,
        "confidence": verification.confidence,
    }
    application.verified_at = datetime.now(timezone.utc)
    
    if not verification.valid:
        application.status = models.ApplicationStatus.REJECTED
        db.commit()
        return schemas.FundTransferResponse(
            status="rejected",
            donation_id=str(donation.id),
            verification_result=application.genai_result,
        )

    # Fund transfer ho raha hai, toh balance update karna padega
    donation.remaining_amount = float(donation.remaining_amount) - request.amount
    
    # Create Transfer Record
    transfer = models.FundTransferRecord(
        donation_id=donation.id,
        amount=request.amount,
        purpose=request.purpose,
        tx_hash=f"SIMULATED_TX_{uuid_module.uuid4()}",
        confirmed=True,
        confirmed_at=datetime.now(timezone.utc)
    )
    db.add(transfer)
    
    db.commit()

    return schemas.FundTransferResponse(
        status="success",
        tx_hash=transfer.tx_hash,
        donation_id=str(donation.id),
        remaining_funds=float(donation.remaining_amount),
        verification_result=application.genai_result,
    )



@app.get("/api/debug/db-state")
def get_db_state(db: Session = Depends(get_db)):
    # Saari tables ka state ek saath dekhne ke liye (DEBUG ONLY)
    users = db.query(models.User).all()
    ngos = db.query(models.NGO).all()
    donations = db.query(models.Donation).all()
    transfers = db.query(models.FundTransferRecord).all()
    applications = db.query(models.ScholarshipApplication).all()

    return {
        "users": [{"id": str(u.id), "email": u.email, "role": u.role} for u in users],
        "ngos": [{"id": str(n.id), "name": n.name, "net_funding": float(n.net_funding)} for n in ngos],
        "donations": [{"id": str(d.id), "amount": float(d.amount), "remaining": float(d.remaining_amount), "donor_id": str(d.donator_id), "ngo_id": str(d.ngo_id)} for d in donations],
        "transfers": [{"id": str(t.id), "amount": float(t.amount), "donation_id": str(t.donation_id)} for t in transfers],
        "applications": [{"id": str(a.id), "status": a.status.value, "verified_by_genai": a.verified_by_genai} for a in applications],
    }

@app.get("/api/blockchain/remaining-funds/{donation_id}", response_model=schemas.RemainingFundsResponse)
def get_remaining_funds(donation_id: str, db: Session = Depends(get_db)):
    """Returns remaining usable funds from the DB."""
    donation = db.query(models.Donation).filter(models.Donation.id == uuid_module.UUID(donation_id)).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
        
    return schemas.RemainingFundsResponse(
        donation_id=donation_id,
        remaining_funds=float(donation.remaining_amount),
        fully_used=float(donation.remaining_amount) <= 0,
    )


@app.get("/api/transactions/me", response_model=List[schemas.TransactionRecord])
def get_my_transactions(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # User ke hisab se saari history nikaalo (Donor/NGO/Student)
    transactions: List[schemas.TransactionRecord] = []

    if current_user.role == models.UserRole.DONATOR:
        profile = db.query(models.DonatorProfile).filter(models.DonatorProfile.user_id == current_user.id).first()
        if profile:
            donations = db.query(models.Donation).filter(models.Donation.donator_id == profile.id).all()
            for d in donations:
                transactions.append(
                    schemas.TransactionRecord(
                        purpose=100,
                        donation_id=str(d.id),
                        sender_id=str(current_user.id),
                        receiver_id=str(d.ngo_id),
                        amount=float(d.amount),
                        timestamp=d.donated_at.isoformat(),
                        tx_type="DONOR_TO_NGO"
                    )
                )
    elif current_user.role == models.UserRole.STUDENT:
        # Complex join not strict required for mock, just simulate
        pass
    elif current_user.role == models.UserRole.NGO_PERSONNEL:
        ngo_personnel = db.query(models.NGOPersonnel).filter(models.NGOPersonnel.user_id == current_user.id).first()
        if ngo_personnel:
            received = db.query(models.Donation).filter(models.Donation.ngo_id == ngo_personnel.ngo_id).all()
            for d in received:
                transactions.append(
                    schemas.TransactionRecord(
                        purpose=100,
                        donation_id=str(d.id),
                        sender_id=str(d.donator_id),
                        receiver_id=str(d.ngo_id),
                        amount=float(d.amount),
                        timestamp=d.donated_at.isoformat(),
                        tx_type="RECEIVED"
                    )
                )

    transactions.sort(key=lambda x: x.timestamp, reverse=True)
    return transactions


@app.get("/api/transactions/ledger", response_model=schemas.LedgerResponse)
def get_ledger(db: Session = Depends(get_db)):
    # Poora ledger merge karke frontend ko bhejo
    donations = db.query(models.Donation).all()
    transfers = db.query(models.FundTransferRecord).all()
    
    transactions: List[schemas.TransactionRecord] = []
    
    for d in donations:
        transactions.append(
            schemas.TransactionRecord(
                purpose=100,
                donation_id=str(d.id),
                sender_id=str(d.donator_id),
                receiver_id=str(d.ngo_id),
                amount=float(d.amount),
                timestamp=d.donated_at.isoformat(),
                tx_type="DONOR_TO_NGO"
            )
        )
        
    for t in transfers:
        transactions.append(
            schemas.TransactionRecord(
                purpose=t.purpose,
                donation_id=str(t.donation_id),
                sender_id="ngo",
                receiver_id="student",
                amount=float(t.amount),
                timestamp=t.created_at.isoformat(),
                tx_type="NGO_TO_STUDENT"
            )
        )
    
    transactions.sort(key=lambda x: x.timestamp, reverse=True)
    return schemas.LedgerResponse(
        transactions=transactions[:50],
        count=len(transactions)
    )

# ── Student Fund Endpoints ───────────────────────────────────

@app.get("/api/student/funds-received")
def get_student_funds_received(
    current_user: models.User = Depends(auth.get_current_user),
):
    """Returns total funds received by a student from blockchain."""
    if current_user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can access this")
    
    try:
        payments = blockchain.get_uid_payment_data(
            current_user.blockchain_uid, "STUDENT", "R"
        )
        total = sum(int(p["amount"]) for p in payments)
    except Exception as e:
        print(f"Error fetching student blockchain data: {e}")
        total = 0
    
    return {"total_received": total}


# ── Scholarship Endpoints ────────────────────────────────────

@app.get("/api/scholarships", response_model=List[schemas.ScholarshipSchemeResponse])
def list_scholarships(db: Session = Depends(get_db)):
    """Returns all available scholarship schemes."""
    schemes = db.query(models.ScholarshipScheme, models.NGO.name.label("ngo_name")).join(
        models.NGO, models.ScholarshipScheme.ngo_id == models.NGO.id
    ).all()
    
    result = []
    for s_obj, ngo_name in schemes:
        s = s_obj
        result.append(schemas.ScholarshipSchemeResponse(
            id=str(s.id),
            ngo_id=str(s.ngo_id),
            ngo_name=ngo_name,
            title=s.title,
            description=s.description,
            amount_per_student=float(s.amount_per_student),
            contract_address=s.contract_address,
            scheme_beneficiary=s.scheme_beneficiary,
            deadline=s.deadline.isoformat() if s.deadline else None
        ))
    return result

@app.post("/api/scholarships/apply", response_model=schemas.ScholarshipApplicationResponse)
def apply_for_scholarship(
    request: schemas.ScholarshipApplicationCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Allows a student to apply for a scholarship scheme."""
    if current_user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can apply for scholarships")

    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Check if already applied
    existing = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.scheme_id == uuid.UUID(request.scheme_id),
        models.ScholarshipApplication.student_id == profile.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this scheme")

    new_app = models.ScholarshipApplication(
        scheme_id=uuid.UUID(request.scheme_id),
        student_id=profile.id,
        status=models.ApplicationStatus.SUBMITTED,
        documents=request.documents
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    return schemas.ScholarshipApplicationResponse(
        id=str(new_app.id),
        scheme_id=str(new_app.scheme_id),
        student_id=str(new_app.student_id),
        status=new_app.status.value,
        applied_at=new_app.applied_at.isoformat(),
        documents=new_app.documents
    )



@app.websocket("/ws/ledger")
async def websocket_ledger(websocket: WebSocket):
    """
    Real-time Transparent Ledger updates.
    Pushes new_transaction and blockchain_event messages.
    """
    await ws_manager.connect(websocket, "ledger")
    try:
        while True:
            # Keep connection alive — client may send heartbeats
            data = await websocket.receive_text()
            # Echo back as heartbeat acknowledgement
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "ledger")


@app.websocket("/ws/donor/{user_id}")
async def websocket_donor(websocket: WebSocket, user_id: str):
    """
    Per-donor real-time updates.
    Pushes donation confirmations, student funded notifications.
    """
    channel = f"donor:{user_id}"
    await ws_manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)


from app import blockchain

ROLE_TO_CLIENT_TYPE = {
    "DONATOR": "DONOR",
    "NGO_PERSONNEL": "NGO",
    "STUDENT": "STUDENT",
}

# Operation code per role:
# DONOR sends funds (operation "D" = outgoing/sender)
# NGO receives funds (operation "R" = incoming/receiver)
# STUDENT receives funds (operation "R" = incoming/receiver)
ROLE_TO_OPERATION = {
    "DONATOR": "D",
    "NGO_PERSONNEL": "R",
    "STUDENT": "R",
}


@app.get("/api/blockchain/my-transactions")
def get_my_blockchain_transactions(current_user: models.User = Depends(auth.get_current_user)):
    """
    Fetch blockchain payment data for the current user.
    - UID is fetched from DB (JWT → user → blockchain_uid). Frontend NEVER controls UID.
    - clientType is mapped: DONATOR→DONOR, NGO_PERSONNEL→NGO, STUDENT→STUDENT
    - operation: DONOR→"D" (sender), NGO/STUDENT→"R" (receiver)
    Returns tuple[] from contract: (purpose, donationId, senderUID, receiverUID, amount, timeStamp)
    """
    try:
        role_value = current_user.role.value  # e.g. "DONATOR", "NGO_PERSONNEL", "STUDENT"
        client_type = ROLE_TO_CLIENT_TYPE.get(role_value)
        op_code = ROLE_TO_OPERATION.get(role_value)

        if not client_type or not op_code:
            print(f"Unknown role for blockchain mapping: {role_value}")
            return []

        uid = current_user.blockchain_uid  # Stable, assigned once at user creation
        print(f"[Blockchain] getUIDPaymentData(uid={uid}, clientType={client_type}, operation={op_code})")

        data = blockchain.get_uid_payment_data(uid, client_type, op_code)

        # Enrich each record with tx_type for frontend display
        tx_type = "DONOR_TO_NGO" if role_value == "DONATOR" else "NGO_TO_STUDENT"
        for d in data:
            d["tx_type"] = tx_type
            # purpose=100 means donation (donor→NGO), treat as null purpose for display

        return data
    except Exception as e:
        import traceback
        print(f"Blockchain fetch error: {e}")
        traceback.print_exc()
        return []


@app.get("/api/blockchain/remaining-funds-bc/{donation_id}")
def remaining_funds_bc(donation_id: int):
    """Get remaining funds for a blockchain donationId (integer)."""
    try:
        rem = blockchain.get_remaining_funds(donation_id)
        return {"donation_id": donation_id, "remaining_funds": rem, "fully_used": rem == 0}
    except Exception as e:
        print(f"Blockchain remaining funds error for donation {donation_id}: {e}")
        return {"donation_id": donation_id, "remaining_funds": 0, "fully_used": False}


@app.get("/api/blockchain/donation/{donation_id}/students")
def get_students_for_donation(donation_id: int):
    """Get students funded by a specific blockchain donationId (integer)."""
    try:
        students = blockchain.get_students_funded_by_donation(donation_id)
        return students
    except Exception as e:
        print(f"Blockchain students fetch error for donation {donation_id}: {e}")
        return []


@app.get("/api/blockchain/ledger")
def get_blockchain_ledger():
    """
    Get the last 50 transactions from the blockchain (merged donor + NGO).
    Uses last50Transactions() — onlyOwner view function.
    """
    try:
        data = blockchain.get_last_50_transactions()
        # Classify each transaction by purpose
        for d in data:
            d["tx_type"] = "DONOR_TO_NGO" if d.get("purpose") == 100 else "NGO_TO_STUDENT"
        return {"transactions": data, "count": len(data)}
    except Exception as e:
        import traceback
        print(f"Blockchain ledger fetch error: {e}")
        traceback.print_exc()
        return {"transactions": [], "count": 0}

# Production mein built frontend files serve karne ka jugaad
dist_path = os.path.join(os.path.dirname(__file__), "..", "dist")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip if it starts with api or ws (already handled by routers/websocket)
    if full_path.startswith("api") or full_path.startswith("ws"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Path to the requested file in dist
    file_path = os.path.join(dist_path, full_path)
    
    # If it's a file that exists, serve it
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, serve index.html for client-side routing (React Router)
    index_path = os.path.join(dist_path, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    
    return {"message": "Frontend not built yet. Run 'npm run build'."}
