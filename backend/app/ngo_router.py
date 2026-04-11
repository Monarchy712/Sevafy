from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid as uuid_module
from pydantic import BaseModel
from app import models, auth, blockchain
from app.database import get_db

# Frontend ko data bhejne wale schemas

class NGOStatsResponse(BaseModel):
    ngo_id: str
    ngo_name: str
    blockchain_uid: int
    net_funding: float
    total_disbursed: float
    scholarships_count: int
    amount_per_student_avg: float
    utilization_rate: float  # total_disbursed / net_funding
    impact_rating: float     # Weighted score 1.0 – 5.0
    impact_label: str        # "Platinum", "Gold", "Silver", "Bronze", "Emerging"

class DonationRecord(BaseModel):
    donation_no: str         # e.g. "#12"
    sender_uid: str
    receiver_uid: str
    amount: float
    timestamp: str           # Formatted date
    tx_hash: Optional[str] = None

class ScholarshipSummary(BaseModel):
    donation_no: str
    sender_uid: str
    receiver_uid: str
    amount: float
    timestamp: str
    purpose: str
    application_id: Optional[str] = None # For DB link
    status: Optional[str] = None         # For DB link (e.g. SUBMITTED)

class InstallmentDetail(BaseModel):
    phase: int
    phase_name: str
    amount: float
    is_disbursed: bool
    disbursed_at: Optional[str] = None
    tx_hash: Optional[str] = None

class ScholarshipDetailResponse(BaseModel):
    application_id: str
    student_name: str
    institution_name: Optional[str]
    course: Optional[str]
    annual_family_income: Optional[float]
    scheme_title: str
    amount_per_student: float
    status: str
    applied_at: str
    verified_by_genai: Optional[bool]
    genai_result: Optional[dict]
    documents: Optional[dict]
    installments: List[InstallmentDetail]

class SuccessResponse(BaseModel):
    success: bool
    message: str
    tx_hash: Optional[str] = None

# Installment phases ke naam ka map
PHASE_NAMES = {
    0:  "New Admission",
    1:  "Mid-Term Installment",
    2:  "Academic Renewal",
    3:  "Completion Status",
    4:  "Study Material Support",
    5:  "Hostel / Living Expense",
    6:  "Emergency Support",
    7:  "Dropout Recovery Support",
    8:  "Skill & Certification Support",
    9:  "Device / Tech Support",
    10: "Performance Incentive",
    11: "Special Category Support",
}

# NGO ka impact score calculate karne ka logic
def calculate_impact_rating(
    net_funding: float,
    total_disbursed: float,
    scholarships_count: int,
    amount_per_student_avg: float,
) -> tuple[float, str]:
    """
    Weighted NGO Impact Score (1.0 – 5.0)

    Components & Weights:
    ┌─────────────────────────────┬────────┬────────────────────────────────────────┐
    │ Component                   │ Weight │ Description                            │
    ├─────────────────────────────┼────────┼────────────────────────────────────────┤
    │ Utilization Rate            │  40%   │ How much of funding was actually used  │
    │ Scale (scholarships count)  │  30%   │ Number of students supported           │
    │ Per-Student Amount          │  20%   │ Quality / depth of support             │
    │ Fund Mobilization           │  10%   │ Absolute fundraising capability        │
    └─────────────────────────────┴────────┴────────────────────────────────────────┘
    """
    # 1. Utilization Rate (0-1 → normalized to 0-5)
    utilization = min(total_disbursed / net_funding, 1.0) if net_funding > 0 else 0.0
    utilization_score = utilization * 5.0

    # 2. Scale Score (log-normalized: 50 scholarships = ~5.0 score)
    import math
    scale_score = min(math.log1p(scholarships_count) / math.log1p(50) * 5.0, 5.0)

    # 3. Per-Student Quality (₹50,000 per student = 5.0 score)
    quality_score = min(amount_per_student_avg / 50_000 * 5.0, 5.0)

    # 4. Fund Mobilization (₹1 crore = 5.0 score)
    mobilization_score = min(net_funding / 10_000_000 * 5.0, 5.0)

    # Weighted composite
    final_score = (
        utilization_score  * 0.40 +
        scale_score        * 0.30 +
        quality_score      * 0.20 +
        mobilization_score * 0.10
    )
    final_score = round(final_score, 2)

    # Label
    if final_score >= 4.5:
        label = "Platinum"
    elif final_score >= 3.5:
        label = "Gold"
    elif final_score >= 2.5:
        label = "Silver"
    elif final_score >= 1.5:
        label = "Bronze"
    else:
        label = "Emerging"

    return final_score, label


# NGO portal ke saari routes yahan hain
router = APIRouter(prefix="/ngo", tags=["NGO Portal"])


def _get_ngo_for_user(current_user, db):
    # Check karo ki ye user sahi NGO personnel hai ya nahi
    from app import models  # Imported here to keep the file self-contained

    if current_user.role.value != "NGO_PERSONNEL":
        raise HTTPException(status_code=403, detail="Access restricted to NGO Personnel only.")

    personnel = db.query(models.NGOPersonnel).filter(
        models.NGOPersonnel.user_id == current_user.id
    ).first()

    if not personnel:
        raise HTTPException(
            status_code=404,
            detail="No NGO is linked to your account. Contact Sevafy admin."
        )

    ngo = db.query(models.NGO).filter(models.NGO.id == personnel.ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO record not found.")

    return ngo


@router.get("/stats", response_model=NGOStatsResponse)
def get_ngo_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return get_ngo_stats_live(current_user, db)


@router.get("/stats/live", response_model=NGOStatsResponse)
def get_ngo_stats_live(current_user, db):
    from app import models, blockchain
    from datetime import datetime

    ngo = _get_ngo_for_user(current_user, db)
    
    # 1. Fetch on-chain data
    try:
        received = blockchain.get_uid_payment_data(ngo.blockchain_uid, "NGO", "R")
        disbursed = blockchain.get_uid_payment_data(ngo.blockchain_uid, "NGO", "D")
    except Exception as e:
        print(f"Error fetching chain data: {e}")
        received = []
        disbursed = []

    # 2. Calculate KPIs from chain data
    net_funding = sum(float(tx["amount"] or 0) for tx in received)
    total_disbursed = sum(float(tx["amount"] or 0) for tx in disbursed)
    
    # 3. Calculate Scholarships Approved count
    # Source A: Unique student UIDs in the on-chain "D" list
    onchain_student_uids = {tx["receiver_uid"] for tx in disbursed}
    
    # Source B: APPROVED applications in DB (for immediate updates before indexing)
    schemes = db.query(models.ScholarshipScheme).filter(models.ScholarshipScheme.ngo_id == ngo.id).all()
    scheme_ids = [s.id for s in schemes]
    db_approved_count = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.scheme_id.in_(scheme_ids),
        models.ScholarshipApplication.status == models.ApplicationStatus.APPROVED
    ).count() if scheme_ids else 0
    
    # Use max to ensure we capture both legacy on-chain data and new DB approvals
    scholarships_count = max(len(onchain_student_uids), db_approved_count)

    # 4. Handle Avg. Amount: total disbursed / count of approved scholarships
    avg_per_student = 0.0
    if scholarships_count > 0:
        avg_per_student = total_disbursed / scholarships_count

    utilization = total_disbursed / net_funding if net_funding > 0 else 0.0

    if total_disbursed == 0:
        impact_score = 0.0
        label = "Emerging"
    else:
        impact_score, label = calculate_impact_rating(
            net_funding=net_funding,
            total_disbursed=total_disbursed,
            scholarships_count=scholarships_count,
            amount_per_student_avg=avg_per_student,
        )

    return NGOStatsResponse(
        ngo_id=str(ngo.id),
        ngo_name=ngo.name,
        blockchain_uid=ngo.blockchain_uid,
        net_funding=net_funding,
        total_disbursed=total_disbursed,
        scholarships_count=scholarships_count,
        amount_per_student_avg=avg_per_student,
        utilization_rate=round(utilization, 4),
        impact_rating=impact_score,
        impact_label=label,
    )


@router.get("/donations", response_model=List[DonationRecord])
def get_incoming_donations(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # NGO ko kitni donations mili unki list
    from app import models, blockchain
    def format_ts(ts):
        from datetime import datetime
        if isinstance(ts, int): return datetime.fromtimestamp(ts).strftime("%d %B %Y, %H:%M")
        try: return datetime.fromisoformat(ts).strftime("%d %B %Y, %H:%M")
        except: return str(ts)

    ngo = _get_ngo_for_user(current_user, db)
    
    try:
        onchain_donations = blockchain.get_uid_payment_data(ngo.blockchain_uid, "NGO", "R")
        onchain_donations = onchain_donations[::-1] # Show latest first
    except Exception as e:
        print(f"Error fetching chain donations: {e}")
        onchain_donations = []

    # Map to DonationRecord
    result = []
    for d in onchain_donations:
        result.append(DonationRecord(
            donation_no=f"#{d['donation_id']}",
            sender_uid=str(d['sender_uid']) if d['sender_uid'] else "Unknown",
            receiver_uid=f"{ngo.name}", # Show NGO Name per request
            amount=float(d['amount']),
            timestamp=format_ts(d['timestamp']),
            tx_hash=None
        ))
    return result


@router.get("/scholarships", response_model=List[ScholarshipSummary])
def get_ongoing_scholarships(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # NGO ke under jitni bhi pending scholarships hain
    from app import models, blockchain
    def format_ts(ts):
        from datetime import datetime
        if isinstance(ts, int): return datetime.fromtimestamp(ts).strftime("%d %B %Y, %H:%M")
        try: return datetime.fromisoformat(ts).strftime("%d %B %Y, %H:%M")
        except: return str(ts)

    ngo = _get_ngo_for_user(current_user, db)

    # 1. Fetch on-chain disbursements
    try:
        onchain_disbursed = blockchain.get_uid_payment_data(ngo.blockchain_uid, "NGO", "D")
    except Exception as e:
        print(f"Error fetching chain disbursements: {e}")
        onchain_disbursed = []

    # 2. Fetch all schemes for this NGO
    schemes = db.query(models.ScholarshipScheme).filter(models.ScholarshipScheme.ngo_id == ngo.id).all()
    scheme_ids = [s.id for s in schemes]

    # Pre-process on-chain data and match to applications
    disbursed_results = []
    seen_application_ids = set()
    student_uid_map = {} # Cache for student UID -> app_id

    for d in onchain_disbursed[::-1]: # Latest on-chain first
        target_uid = d['receiver_uid']
        app_id_found = None
        
        if target_uid not in student_uid_map:
            student_profile = db.query(models.StudentProfile).filter(models.StudentProfile.blockchain_uid == target_uid).first()
            if student_profile:
                # Find matching application — use student_id AND the donation_id_used for accuracy
                app = db.query(models.ScholarshipApplication).filter(
                    models.ScholarshipApplication.student_id == student_profile.id,
                    models.ScholarshipApplication.scheme_id.in_(scheme_ids),
                    models.ScholarshipApplication.donation_id_used == d['donation_id']
                ).first()
                # Fallback to just student/scheme if donation_id_used is missing (old records)
                if not app:
                    app = db.query(models.ScholarshipApplication).filter(
                        models.ScholarshipApplication.student_id == student_profile.id,
                        models.ScholarshipApplication.scheme_id.in_(scheme_ids)
                    ).first()
                if app:
                    app_id_found = str(app.id)
                    seen_application_ids.add(app_id_found)
            student_uid_map[target_uid] = app_id_found
        else:
            app_id_found = student_uid_map[target_uid]
            if app_id_found:
                seen_application_ids.add(app_id_found)

        disbursed_results.append(ScholarshipSummary(
            donation_no=f"#{d['donation_id']}",
            sender_uid=f"{ngo.name}", # Show NGO Name per request
            receiver_uid=str(d['receiver_uid']),
            amount=float(d['amount']),
            timestamp=format_ts(d['timestamp']),
            purpose=PHASE_NAMES.get(d['purpose'], f"Phase {d['purpose']}"),
            application_id=app_id_found,
            status="DISBURSED"
        ))

    # 3. Fetch pending/approved applications from DB
    pending_apps = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.scheme_id.in_(scheme_ids),
        models.ScholarshipApplication.status.in_([models.ApplicationStatus.SUBMITTED, models.ApplicationStatus.APPROVED])
    ).all() if scheme_ids else []

    app_results = []
    for app in pending_apps:
        # CRITICAL FIX: If the application is already showing up on-chain,
        # don't show the duplicate "PROCESSING" row.
        if app.status == models.ApplicationStatus.APPROVED and str(app.id) in seen_application_ids:
            continue

        student_profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == app.student_id).first()
        student_uid = student_profile.blockchain_uid if student_profile else 0
        scheme = db.query(models.ScholarshipScheme).filter(models.ScholarshipScheme.id == app.scheme_id).first()
        amount = float(scheme.amount_per_student) if scheme else 0.0
        
        app_results.append(ScholarshipSummary(
            donation_no="PENDING" if app.status == models.ApplicationStatus.SUBMITTED else "PROCESSING",
            sender_uid=f"{ngo.name}({ngo.blockchain_uid})",
            receiver_uid=f"Student({student_uid})",
            amount=amount,
            timestamp=app.applied_at.strftime("%d %B %Y"),
            purpose="Scholarship Approval",
            application_id=str(app.id),
            status=app.status.value
        ))

    # Combine: Pending at top, then on-chain history
    return app_results + disbursed_results


@router.post("/scholarships/{application_id}/approve", response_model=SuccessResponse)
def approve_scholarship(
    application_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    from app import models, blockchain
    import uuid
    
    ngo = _get_ngo_for_user(current_user, db)
    
    try:
        app_id = uuid.UUID(application_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid application ID")
        
    application = db.query(models.ScholarshipApplication).filter(models.ScholarshipApplication.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != models.ApplicationStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Application already processed")
        
    # Verify NGO ownership
    scheme = db.query(models.ScholarshipScheme).filter(
        models.ScholarshipScheme.id == application.scheme_id,
        models.ScholarshipScheme.ngo_id == ngo.id
    ).first()
    if not scheme:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    scholarship_amount = int(scheme.amount_per_student)
    
    # Scheme ke description se automatically purpose pehchano
    text = ((scheme.title or "") + " " + (scheme.description or "") + " " + (scheme.scheme_beneficiary or "")).lower()
    
    if any(kw in text for kw in ["device", "laptop", "tablet", "tech", "computer"]):
        purpose = 9   # DEVICE_OR_TECH_SUPPORT
    elif any(kw in text for kw in ["merit", "excellence", "academic", "topper", "performance"]):
        purpose = 10  # PERFORMANCE_INCENTIVE
    elif any(kw in text for kw in ["hostel", "living", "housing", "accommodation"]):
        purpose = 5   # HOSTEL_OR_LIVING_EXPENSE
    elif any(kw in text for kw in ["book", "material", "supply", "stationery"]):
        purpose = 4   # STUDY_MATERIAL_SUPPORT
    elif any(kw in text for kw in ["skill", "certification", "vocational", "training"]):
        purpose = 8   # SKILL_OR_CERTIFICATION_SUPPORT
    elif any(kw in text for kw in ["tuition", "fee", "admission"]):
        purpose = 2   # ACADEMIC_RENEWAL (tuition installment)
    elif any(kw in text for kw in ["dropout", "recovery", "reentry"]):
        purpose = 7   # DROPOUT_RECOVERY_SUPPORT
    elif any(kw in text for kw in ["emergency", "crisis", "urgent"]):
        purpose = 6   # EMERGENCY_SUPPORT
    elif any(kw in text for kw in ["special", "minority", "differently abled", "tribal"]):
        purpose = 11  # SPECIAL_CATEGORY_SUPPORT
    # Donation split logic: ek se zyada donation use karke fund poora karo
    donations = db.query(models.Donation).filter(
        models.Donation.ngo_id == ngo.id,
        models.Donation.confirmed == True,
        models.Donation.remaining_amount > 0
    ).order_by(models.Donation.donated_at.asc()).all()
    
    # Calculate total available funds across all donations
    total_available = sum(int(d.remaining_amount) for d in donations)
    
    if total_available < scholarship_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Available: ₹{total_available:,}, Required: ₹{scholarship_amount:,}. Please wait for more donations."
        )
    
    # ── Get student blockchain UID ──
    student_profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.id == application.student_id
    ).first()
    student_user = db.query(models.User).filter(
        models.User.id == student_profile.user_id
    ).first() if student_profile else None
    
    if not student_user:
        raise HTTPException(status_code=404, detail="Student user not found")
    
    student_uid = student_user.blockchain_uid
    # Blockchain call loop: har chunk ko on-chain transfer karo
    remaining_to_fund = scholarship_amount
    tx_hashes = []
    
    for donation in donations:
        if remaining_to_fund <= 0:
            break
        
        avail = int(donation.remaining_amount)
        chunk = min(avail, remaining_to_fund)
        
        # Verify on-chain remaining funds (smart contract is source of truth)
        try:
            onchain_remaining = blockchain.get_remaining_funds(donation.blockchain_donation_id)
            if onchain_remaining < chunk:
                chunk = onchain_remaining
                if chunk <= 0:
                    continue
        except Exception as e:
            print(f"Warning: Could not verify on-chain funds for donation {donation.blockchain_donation_id}: {e}")
        
        # Call blockchain fundTransfer
        try:
            result = blockchain.call_fund_transfer(
                donation_id=donation.blockchain_donation_id,
                ngo_uid=ngo.blockchain_uid,
                student_uid=student_uid,
                amount=chunk,
                purpose=purpose,
            )
            tx_hash = result["tx_hash"]
            tx_hashes.append(tx_hash)
        except Exception as e:
            print(f"Blockchain transfer failed for donation {donation.blockchain_donation_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Blockchain transfer failed: {str(e)}"
            )
        
        # Update DB donation remaining amount
        donation.remaining_amount = donation.remaining_amount - chunk
        
        # Create FundTransferRecord
        transfer_record = models.FundTransferRecord(
            donation_id=donation.id,
            blockchain_donation_id=donation.blockchain_donation_id,
            ngo_blockchain_uid=ngo.blockchain_uid,
            student_blockchain_uid=student_uid,
            amount=chunk,
            purpose=purpose,
            tx_hash=tx_hash,
            confirmed=True,
            confirmed_at=func.now(),
        )
        db.add(transfer_record)
        
        remaining_to_fund -= chunk
    
    # ── Update application status ──
    application.status = models.ApplicationStatus.APPROVED
    application.donation_id_used = donations[0].blockchain_donation_id if donations else None
    db.commit()
    
    final_tx = tx_hashes[-1] if tx_hashes else None
    return SuccessResponse(
        success=True,
        message=f"Scholarship approved and ₹{scholarship_amount:,} transferred to student on-chain.",
        tx_hash=final_tx,
    )


@router.get("/scholarships/{application_id}", response_model=ScholarshipDetailResponse)
def get_scholarship_detail(
    application_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full detail view for a single scholarship application including the 12-phase tracker.
    Integration: wire in Depends(auth.get_current_user) and Depends(get_db).
    """
    from app import models

    ngo = _get_ngo_for_user(current_user, db)

    try:
        app_uuid = uuid_module.UUID(application_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application ID format.")

    application = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.id == app_uuid
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Verify this application belongs to an NGO scheme this user manages
    scheme = db.query(models.ScholarshipScheme).filter(
        models.ScholarshipScheme.id == application.scheme_id,
        models.ScholarshipScheme.ngo_id == ngo.id
    ).first()
    if not scheme:
        raise HTTPException(status_code=403, detail="This application does not belong to your NGO.")

    # Student details
    student_profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.id == application.student_id
    ).first()
    student_user = db.query(models.User).filter(
        models.User.id == student_profile.user_id
    ).first() if student_profile else None

    # Build the 12-phase installment list (fill in dummy phases if not in DB yet)
    db_installments = db.query(models.ScholarshipInstallment).filter(
        models.ScholarshipInstallment.application_id == application.id
    ).all()
    db_phases = {
        (i.phase.value if hasattr(i.phase, 'value') else i.phase): i
        for i in db_installments
    }

    installments_out = []
    for phase_num in range(12):
        phase_name = PHASE_NAMES.get(phase_num, f"Stage {phase_num}")
        db_inst = db_phases.get(phase_num)
        if db_inst:
            installments_out.append(InstallmentDetail(
                phase=phase_num,
                phase_name=phase_name,
                amount=float(db_inst.amount),
                is_disbursed=db_inst.is_disbursed,
                disbursed_at=db_inst.disbursed_at.isoformat() if db_inst.disbursed_at else None,
                tx_hash=db_inst.tx_hash,
            ))
        else:
            # Phase not yet created — show as pending
            installments_out.append(InstallmentDetail(
                phase=phase_num,
                phase_name=phase_name,
                amount=float(scheme.amount_per_student) / 12,  # Split equally as estimate
                is_disbursed=False,
            ))

    return ScholarshipDetailResponse(
        application_id=str(application.id),
        student_name=student_user.full_name if student_user else "Student",
        institution_name=student_profile.institution_name if student_profile else None,
        course=student_profile.course if student_profile else None,
        annual_family_income=float(student_profile.annual_family_income) if student_profile and student_profile.annual_family_income else None,
        scheme_title=scheme.title,
        amount_per_student=float(scheme.amount_per_student),
        status=application.status.value,
        applied_at=application.applied_at.isoformat(),
        verified_by_genai=application.verified_by_genai,
        genai_result=application.genai_result,
        documents=application.documents,
        installments=installments_out,
    )
