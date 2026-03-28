from app.database import engine
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_schema():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables: {tables}")
    
    for table_name in ["users", "ngos"]:
        if table_name in tables:
            columns = [c["name"] for c in inspector.get_columns(table_name)]
            logger.info(f"Columns for {table_name}: {columns}")
            if "blockchain_uid" in columns:
                logger.info(f"✅ 'blockchain_uid' exists in {table_name}")
            else:
                logger.warning(f"❌ 'blockchain_uid' MISSING in {table_name}")
        else:
            logger.error(f"❌ Table {table_name} NOT FOUND")

if __name__ == "__main__":
    check_schema()
