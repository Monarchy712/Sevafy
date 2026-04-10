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
        print("Adding 'blockchain_uid' column to 'student_profiles'...")
        try:
            # 1. Add column
            conn.execute(text('ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS blockchain_uid INTEGER UNIQUE'))
            conn.commit()
            print("Successfully added column.")
            
            # 2. Sync data from users table
            print("Syncing blockchain_uid from users table...")
            conn.execute(text('''
                UPDATE student_profiles
                SET blockchain_uid = users.blockchain_uid
                FROM users
                WHERE student_profiles.user_id = users.id
                  AND student_profiles.blockchain_uid IS NULL
            '''))
            conn.commit()
            print("Successfully synced data.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
