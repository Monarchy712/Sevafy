import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use environment variable or default to the provided Neon PostgreSQL cloud instance
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://neondb_owner:npg_VNZJb9OBw5eA@ep-late-voice-a1bmdqzm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# Create the SQLAlchemy engine for PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Ensure the database tables are created (Metadata handles this for us during startup elsewhere, 
# but it is common practice to initialize the engine here)
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
