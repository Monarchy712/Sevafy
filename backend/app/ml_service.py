import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import models

# Load the model directly when the module is initialized
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_engine', 'ngo_recommender.pkl')

try:
    recommender_model = joblib.load(MODEL_PATH)
except Exception as e:
    recommender_model = None
    print(f"Warning: ML Recommendations model not found at {MODEL_PATH}")

import hashlib

def calculate_ngo_features(db: Session, ngo_id: str):
    # Deterministic variance based on UUID for MVP mock differences
    hash_val = int(hashlib.md5(str(ngo_id).encode()).hexdigest(), 16)
    v1 = (hash_val % 100) / 100.0  # 0.0 - 0.99
    v2 = ((hash_val // 100) % 100) / 100.0
    v3 = ((hash_val // 10000) % 100) / 100.0
    v4 = ((hash_val // 1000000) % 100) / 100.0

    # 1. Funding Ratio
    # Real logic: Total Donations / Total Required by scheme
    # Since MVP database might be empty, we will try to calculate, then fallback gracefully.
    
    donations_sum = db.query(func.sum(models.Donation.amount)).filter(models.Donation.ngo_id == ngo_id).scalar() or 0
    
    total_needed = db.query(
        func.sum(models.ScholarshipScheme.amount_per_student)
    ).join(
        models.ScholarshipApplication, models.ScholarshipApplication.scheme_id == models.ScholarshipScheme.id
    ).filter(
        models.ScholarshipScheme.ngo_id == ngo_id,
        models.ScholarshipApplication.status == "APPROVED"
    ).scalar() or 0

    if total_needed > 0:
        funding_ratio = min(float(donations_sum) / float(total_needed), 1.5)
    else:
        # Cold start fallback for funding ratio (varies per NGO: 0.2 to 0.9)
        funding_ratio = 0.2 + (v1 * 0.7)

    # 2. Avg Student Income
    avg_income = db.query(
        func.avg(models.StudentProfile.annual_family_income)
    ).join(
        models.ScholarshipApplication, models.ScholarshipApplication.student_id == models.StudentProfile.id
    ).join(
        models.ScholarshipScheme, models.ScholarshipScheme.id == models.ScholarshipApplication.scheme_id
    ).filter(
        models.ScholarshipScheme.ngo_id == ngo_id
    ).scalar()

    avg_student_income = float(avg_income) if avg_income else (50000.0 + (v2 * 150000.0))

    # 3. Disbursement Velocity Days
    # Just an MVP placeholder calculation
    disbursement_velocity_days = 5.0 + (v3 * 40.0) 

    # 4. Application Backlog
    application_backlog = db.query(func.count(models.ScholarshipApplication.id)).join(
        models.ScholarshipScheme, models.ScholarshipScheme.id == models.ScholarshipApplication.scheme_id
    ).filter(
        models.ScholarshipScheme.ngo_id == ngo_id,
        models.ScholarshipApplication.status == "APPROVED"
    ).scalar() or int(v4 * 50) # MVP cold start backlog

    return {
        'funding_ratio': funding_ratio,
        'avg_student_income': avg_student_income,
        'disbursement_velocity_days': disbursement_velocity_days,
        'application_backlog': application_backlog
    }

def get_top_ngos(db: Session, ngos: list):
    """
    Takes a list of NGO objects from DB, calculates their features,
    scores them using the XGBoost model, and sorts them.
    """
    if not recommender_model:
        # Fallback if model failed to load or in pure dev mode
        top_5 = []
        for rank, n in enumerate(ngos[:5]):
            top_5.append({
                "ngo": n,
                "impact_score": 0.0,
                "rank": rank + 1,
                "features": {"status": "Model Offline"}
            })
        return top_5

    features_list = []
    for n in ngos:
        feats = calculate_ngo_features(db, n.id)
        features_list.append(feats)

    # Convert to dataframe exactly matching the model training features
    df = pd.DataFrame(features_list)
    
    if df.empty:
        return []

    # Score using XGBoost
    scores = recommender_model.predict(df)
    
    # Attach scores to ngos
    scored_ngos = []
    for i, n in enumerate(ngos):
        scored_ngos.append({
            "ngo": n,
            "impact_score": round(float(scores[i]), 2),
            "features": features_list[i]
        })

    # Sort descending by score
    scored_ngos.sort(key=lambda x: x["impact_score"], reverse=True)

    # Return top 5 with ranking
    top_5 = []
    for rank, item in enumerate(scored_ngos[:5]):
        item["rank"] = rank + 1
        top_5.append(item)

    return top_5
