import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def debug():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    if "ngo_personnel" in tables:
        columns = inspector.get_columns("ngo_personnel")
        print("\nColumns in 'ngo_personnel':")
        for col in columns:
            print(f" - {col['name']} ({col['type']})")
            
    # Try to add missing column if needed
    try:
        with engine.connect() as conn:
            # Check if ngo_personnel has data
            res = conn.execute(text("SELECT COUNT(*) FROM ngo_personnel"))
            count = res.scalar()
            print(f"\nRows in 'ngo_personnel': {count}")
            
            # Check NGOs
            res = conn.execute(text("SELECT COUNT(*) FROM ngos"))
            print(f"Rows in 'ngos': {res.scalar()}")
            
            # Check Users with role NGO_PERSONNEL
            res = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'NGO_PERSONNEL'"))
            print(f"Users with role NGO_PERSONNEL: {res.scalar()}")
            
    except Exception as e:
        print(f"\nExecution Error: {e}")

if __name__ == "__main__":
    debug()
