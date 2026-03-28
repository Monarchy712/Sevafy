import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from .env file
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

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
