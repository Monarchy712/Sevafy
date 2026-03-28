import os
import sys
from sqlalchemy.orm import Session

# Setup path
sys.path.append(os.getcwd())

from app import models
from app.database import SessionLocal
from app.ngo_router import get_ngo_stats_live

def test():
    db = SessionLocal()
    try:
        # Find the linked user
        user = db.query(models.User).filter(models.User.role == "NGO_PERSONNEL").first()
        if not user:
            print("No personnel user found.")
            return

        print(f"Testing stats for user: {user.email}")
        
        # Manually call the live stats function
        stats = get_ngo_stats_live(user, db)
        print("\nSTATS RESPONSE:")
        print(f" NGO: {stats.ngo_name} (UID: {stats.blockchain_uid})")
        print(f" Net Funding: {stats.net_funding}")
        print(f" Total Disbursed: {stats.total_disbursed}")
        print(f" Impact: {stats.impact_label} ({stats.impact_rating})")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nTest failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test()
