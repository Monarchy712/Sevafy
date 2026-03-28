from app.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def patch():
    try:
        with engine.connect() as conn:
            logger.info("Patching users table...")
            conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS blockchain_uid SERIAL'))
            
            logger.info("Patching ngos table...")
            conn.execute(text('ALTER TABLE ngos ADD COLUMN IF NOT EXISTS blockchain_uid SERIAL'))
            
            logger.info("Patching donations table...")
            conn.execute(text('ALTER TABLE donations ADD COLUMN IF NOT EXISTS tx_hash VARCHAR'))
            conn.execute(text('ALTER TABLE donations ADD COLUMN IF NOT EXISTS blockchain_donation_id INTEGER'))
            
            logger.info("Patching scholarship_applications table...")
            conn.execute(text('ALTER TABLE scholarship_applications ADD COLUMN IF NOT EXISTS verified_by_genai BOOLEAN'))
            conn.execute(text('ALTER TABLE scholarship_applications ADD COLUMN IF NOT EXISTS genai_result JSONB'))
            conn.execute(text('ALTER TABLE scholarship_applications ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE'))
            conn.execute(text('ALTER TABLE scholarship_applications ADD COLUMN IF NOT EXISTS donation_id_used INTEGER'))
            
            conn.commit()
            logger.info("Schema patched successfully!")
    except Exception as e:
        logger.error(f"Patch failed: {e}")

if __name__ == "__main__":
    patch()
