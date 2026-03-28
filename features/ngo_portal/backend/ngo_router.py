# NGO Portal API Router — see features/ngo_portal/registry_handoff.md for integration instructions.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid as uuid_module
from pydantic import BaseModel


# ── Import from existing core (do NOT modify these) ──────────────
# These imports assume the router is mounted from within the main app
# context where `app` is the FastAPI instance.
# The integration instructions in registry_handoff.md explain exactly
# how to add `from app import models, auth` and `from app.database import get_db`.

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
    donation_id: str
    donor_name: str          # Anonymized for privacy (first name only)
    amount: float
    donated_at: str
    tx_hash: Optional[str] = None
    confirmed: bool

class ScholarshipSummary(BaseModel):
    application_id: str
    student_name: str
    scheme_title: str
    amount_per_student: float
    status: str
    applied_at: str
    current_phase: Optional[int] = None   # 0-11, None if no installments yet
    phases_completed: int                 # Count of disbursed installment phases
    verified_by_genai: Optional[bool] = None

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
    # These are imported at integration time — see registry_handoff.md
    # current_user: models.User = Depends(auth.get_current_user),
    # db: Session = Depends(get_db),
):
    """
    Returns aggregated impact stats and AI rating for the logged-in NGO.

    INTEGRATION NOTE: When mounting this router, uncomment the Depends parameters
    above and add the imports from app.auth and app.database.
    See registry_handoff.md Step 2 for the exact updated function signature.
    """
    raise HTTPException(
        status_code=501,
        detail="Integration pending. Follow registry_handoff.md to activate this endpoint."
    )


@router.get("/stats/live", response_model=NGOStatsResponse)
def get_ngo_stats_live(current_user, db):
    """
    Internal implementation — called after integration wires in auth & db deps.
    This is the actual logic. Copy this pattern into the integrated version.
    """
    from app import models

    ngo = _get_ngo_for_user(current_user, db)

    # Aggregate scholarship data
    schemes = db.query(models.ScholarshipScheme).filter(
        models.ScholarshipScheme.ngo_id == ngo.id
    ).all()
    scheme_ids = [s.id for s in schemes]

    approved_count = 0
    total_disbursed = 0.0
    amount_per_student_sum = 0.0

    if scheme_ids:
        approved_count = db.query(models.ScholarshipApplication).filter(
            models.ScholarshipApplication.scheme_id.in_(scheme_ids),
            models.ScholarshipApplication.status == models.ApplicationStatus.APPROVED
        ).count()

        disbursed = db.query(
            func.sum(models.ScholarshipInstallment.amount)
        ).join(
            models.ScholarshipApplication,
            models.ScholarshipInstallment.application_id == models.ScholarshipApplication.id
        ).filter(
            models.ScholarshipApplication.scheme_id.in_(scheme_ids),
            models.ScholarshipInstallment.is_disbursed == True
        ).scalar()
        total_disbursed = float(disbursed or 0)

        amount_per_student_sum = sum(float(s.amount_per_student) for s in schemes)

    net_funding = float(ngo.net_funding or 0)
    avg_per_student = (amount_per_student_sum / len(schemes)) if schemes else 0.0
    utilization = total_disbursed / net_funding if net_funding > 0 else 0.0

    impact_score, label = calculate_impact_rating(
        net_funding=net_funding,
        total_disbursed=total_disbursed,
        scholarships_count=approved_count,
        amount_per_student_avg=avg_per_student,
    )

    return NGOStatsResponse(
        ngo_id=str(ngo.id),
        ngo_name=ngo.name,
        blockchain_uid=ngo.blockchain_uid,
        net_funding=net_funding,
        total_disbursed=total_disbursed,
        scholarships_count=approved_count,
        amount_per_student_avg=avg_per_student,
        utilization_rate=round(utilization, 4),
        impact_rating=impact_score,
        impact_label=label,
    )


@router.get("/donations", response_model=List[DonationRecord])
def get_incoming_donations(current_user=None, db=None):
    """
    Returns paginated list of donations received by this NGO.
    Integration: wire in Depends(auth.get_current_user) and Depends(get_db).
    """
    from app import models

    ngo = _get_ngo_for_user(current_user, db)

    donations = db.query(models.Donation).filter(
        models.Donation.ngo_id == ngo.id
    ).order_by(models.Donation.donated_at.desc()).limit(50).all()

    result = []
    for d in donations:
        # Fetch donor name (first name only for privacy)
        profile = db.query(models.DonatorProfile).filter(
            models.DonatorProfile.id == d.donator_id
        ).first()
        donor_name = "Anonymous"
        if profile:
            user = db.query(models.User).filter(
                models.User.id == profile.user_id
            ).first()
            if user:
                parts = user.full_name.strip().split()
                donor_name = parts[0] if parts else "Donor"

        result.append(DonationRecord(
            donation_id=str(d.id),
            donor_name=donor_name,
            amount=float(d.amount),
            donated_at=d.donated_at.isoformat(),
            tx_hash=d.tx_hash,
            confirmed=d.confirmed,
        ))
    return result


@router.get("/scholarships", response_model=List[ScholarshipSummary])
def get_ongoing_scholarships(current_user=None, db=None):
    """
    Returns all scholarship applications linked to this NGO's schemes.
    Integration: wire in Depends(auth.get_current_user) and Depends(get_db).
    """
    from app import models

    ngo = _get_ngo_for_user(current_user, db)

    schemes = db.query(models.ScholarshipScheme).filter(
        models.ScholarshipScheme.ngo_id == ngo.id
    ).all()
    scheme_map = {s.id: s for s in schemes}
    scheme_ids = list(scheme_map.keys())

    if not scheme_ids:
        return []

    applications = db.query(models.ScholarshipApplication).filter(
        models.ScholarshipApplication.scheme_id.in_(scheme_ids)
    ).order_by(models.ScholarshipApplication.applied_at.desc()).all()

    result = []
    for app in applications:
        # Student name
        student_profile = db.query(models.StudentProfile).filter(
            models.StudentProfile.id == app.student_id
        ).first()
        student_user = db.query(models.User).filter(
            models.User.id == student_profile.user_id
        ).first() if student_profile else None
        student_name = student_user.full_name if student_user else "Student"

        # Installment progress
        installments = db.query(models.ScholarshipInstallment).filter(
            models.ScholarshipInstallment.application_id == app.id
        ).all()
        phases_done = sum(1 for i in installments if i.is_disbursed)
        current_phase_val = None
        if installments:
            # Highest phase value present
            current_phase_val = max(i.phase.value if hasattr(i.phase, 'value') else i.phase for i in installments)

        scheme = scheme_map.get(app.scheme_id)
        result.append(ScholarshipSummary(
            application_id=str(app.id),
            student_name=student_name,
            scheme_title=scheme.title if scheme else "Unknown Scheme",
            amount_per_student=float(scheme.amount_per_student) if scheme else 0.0,
            status=app.status.value,
            applied_at=app.applied_at.isoformat(),
            current_phase=current_phase_val,
            phases_completed=phases_done,
            verified_by_genai=app.verified_by_genai,
        ))
    return result


@router.get("/scholarships/{application_id}", response_model=ScholarshipDetailResponse)
def get_scholarship_detail(application_id: str, current_user=None, db=None):
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
