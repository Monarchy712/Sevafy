import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Setup path
import sys
sys.path.append(os.getcwd())

load_dotenv()

def migrate():
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        print("Adding 'documents' column to 'scholarship_applications'...")
        try:
            conn.execute(text('ALTER TABLE scholarship_applications ADD COLUMN IF NOT EXISTS documents JSONB'))
            conn.commit()
            print("Successfully added column.")
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
