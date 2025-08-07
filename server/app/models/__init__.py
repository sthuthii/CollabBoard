# backend/app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Define your database URL (using SQLite for local development)
SQLALCHEMY_DATABASE_URL = "sqlite:///./collabboard.db"

# 2. Create the engine (connects SQLAlchemy to the database)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a session (used for querying DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a base class for model classes to inherit
Base = declarative_base()

# 5. Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
