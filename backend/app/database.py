import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use environment variable or default to the provided Neon PostgreSQL cloud instance
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://neondb_owner:npg_VNZJb9OBw5eA@ep-late-voice-a1bmdqzm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# Fallback gracefully to SQLite if the PostgreSQL connection is refused
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        pass
except Exception:
    import logging
    logging.warning("PostgreSQL connection failed. Falling back to SQLite for MVP deployment.")
    engine = create_engine("sqlite:///./sevafy_mvp.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy models
Base = declarative_base()

# Dependency to yield database sessions per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
