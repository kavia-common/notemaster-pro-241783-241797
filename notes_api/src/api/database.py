"""
Database connection and session management for the NoteMaster Pro API.
Uses SQLAlchemy ORM with PostgreSQL.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Build the database URL from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "appuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "dbuser123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "myapp")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5000")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Override with full URL if provided
if os.getenv("POSTGRES_URL"):
    raw_url = os.getenv("POSTGRES_URL", "").strip('"').strip("'")
    if raw_url and not raw_url.startswith("postgresql://localhost"):
        DATABASE_URL = raw_url

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# PUBLIC_INTERFACE
def get_db():
    """
    Dependency that provides a database session.
    Yields a SQLAlchemy session and ensures it is closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
