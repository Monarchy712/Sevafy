import os
from pydantic import BaseModel
from typing import List

class VerificationResult(BaseModel):
    valid: bool
    reason: str
    confidence: float
    details: dict

def verify_student_documents(
    student_name: str,
    institution_name: str,
    course: str,
    annual_income: float,
    documents: List[dict]
) -> VerificationResult:
    """
    Mock GenAI verifier for simulated environment.
    Always returns valid = True with 0.95 confidence.
    """
    return VerificationResult(
        valid=True,
        reason="Documents pass standard simulated checking criteria.",
        confidence=0.95,
        details={
            "identity_match": True,
            "enrollment_verified": True,
            "income_certificate_valid": True,
            "mocked": True
        }
    )
