import sys
import traceback
import os
import uuid
sys.path.append(os.path.abspath('c:/Users/samya/OneDrive/Desktop/Sevafy2/Sevafy/backend'))
from app.database import SessionLocal
from app import models, auth
try:
    db = SessionLocal()
    email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    hashed_password = auth.get_password_hash("password123")
    u = models.User(email=email, password=hashed_password, full_name="Test", role=models.UserRole.STUDENT)
    db.add(u)
    db.commit()
    db.refresh(u)
    p = models.StudentProfile(user_id=u.id)
    db.add(p)
    db.commit()
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
