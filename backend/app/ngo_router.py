from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid as uuid_module
from pydantic import BaseModel
from app import models, auth, blockchain
from app.database import get_db

# ── Response Schemas (isolated, no pollution of schemas.py) ──────

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
    installments: List[InstallmentDetail]

class SuccessResponse(BaseModel):
    success: bool
    message: str

# ── Phase Name Map (mirrors InstallmentPhase enum) ────────────────
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

# ── Impact Rating Algorithm ────────────────────────────────────────
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


# ── Router Definition ─────────────────────────────────────────────
# NOTE: This is mounted at /api/ngo in the integration step.
# See registry_handoff.md → Step 1.

router = APIRouter(prefix="/ngo", tags=["NGO Portal"])


def _get_ngo_for_user(current_user, db):
    """
    Look up the NGO linked to this NGO_PERSONNEL user via the ngo_personnel table.
    Raises 403 if user is not NGO_PERSONNEL, 404 if not linked to any NGO.
    """
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
    
    # Scholarships count = count of unique student UIDs in the "D" list
    student_uids = {tx["receiver_uid"] for tx in disbursed}
    scholarships_count = len(student_uids)

    # 3. Handle Avg. Amount (Only if disbursements exist, otherwise 0 per user request)
    avg_per_student = 0.0
    if total_disbursed > 0 and len(disbursed) > 0:
        avg_per_student = total_disbursed / len(disbursed)

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
    """
    Returns paginated list of donations received by this NGO.
    Integration: wire in Depends(auth.get_current_user) and Depends(get_db).
    """
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
    """
    Returns all scholarship applications linked to this NGO's schemes.
    Integration: wire in Depends(auth.get_current_user) and Depends(get_db).
    """
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

    # 2. Fetch pending applications from DB
    schemes = db.query(models.ScholarshipScheme).filter(models.ScholarshipScheme.ngo_id == ngo.id).all()
    scheme_ids = [s.id for s in schemes]
    pending_apps = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.scheme_id.in_(scheme_ids),
        models.ScholarshipApplication.status == models.ApplicationStatus.SUBMITTED
    ).all() if scheme_ids else []

    result = []
    
    # Add pending apps first (so they are at the top for approval)
    for app in pending_apps:
        # Try to find student UID
        student_profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == app.student_id).first()
        student_uid = student_profile.blockchain_uid if student_profile else 0
        
        result.append(ScholarshipSummary(
            donation_no="PENDING",
            sender_uid=f"{ngo.name}({ngo.blockchain_uid})",
            receiver_uid=f"Student({student_uid})",
            amount=float(app.amount_per_student_avg) if hasattr(app, 'amount_per_student_avg') else 0.0,
            timestamp=app.applied_at.strftime("%d %B %Y"),
            purpose="Scholarship Approval",
            application_id=str(app.id),
            status="SUBMITTED"
        ))

    # Add on-chain disbursed records
    student_uid_map = {} # Cache
    
    for d in onchain_disbursed:
        target_uid = d['receiver_uid']
        app_id = None
        
        if target_uid not in student_uid_map:
            student_profile = db.query(models.StudentProfile).filter(models.StudentProfile.blockchain_uid == target_uid).first()
            if student_profile:
                # Find application for this student in one of this NGO's schemes
                app = db.query(models.ScholarshipApplication).filter(
                    models.ScholarshipApplication.student_id == student_profile.id,
                    models.ScholarshipApplication.scheme_id.in_(scheme_ids)
                ).first()
                if app:
                    app_id = str(app.id)
            student_uid_map[target_uid] = app_id
        else:
            app_id = student_uid_map[target_uid]

        result.append(ScholarshipSummary(
            donation_no=f"#{d['donation_id']}",
            sender_uid=f"{ngo.name}", # Show NGO Name per request
            receiver_uid=str(d['receiver_uid']),
            amount=float(d['amount']),
            timestamp=format_ts(d['timestamp']),
            purpose=PHASE_NAMES.get(d['purpose'], f"Phase {d['purpose']}"),
            application_id=app_id,
            status="DISBURSED"
        ))

    return result


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
        
    # Verify NGO ownership
    scheme = db.query(models.ScholarshipScheme).filter(
        models.ScholarshipScheme.id == application.scheme_id,
        models.ScholarshipScheme.ngo_id == ngo.id
    ).first()
    if not scheme:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    application.status = models.ApplicationStatus.APPROVED
    db.commit()
    
    # Record verification on-chain
    student_profile = db.query(models.StudentProfile).filter(models.StudentProfile.id == application.student_id).first()
    if student_profile and student_profile.blockchain_uid:
        try:
            blockchain.call_record_verification(student_profile.blockchain_uid, "NGO_APPROVAL", True)
        except Exception as e:
            print(f"Failed to record on-chain verification: {e}")
            
    return SuccessResponse(success=True, message="Scholarship approved successfully")


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
        installments=installments_out,
    )
