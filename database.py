from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings
from datetime import datetime

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    native_lang = Column(String, default="")
    target_lang = Column(String, default="")
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    streak_history = Column(JSON, default=lambda: [False, False, False, False, False, False, False])
    sessions_completed = Column(Integer, default=0)
    focus_seconds = Column(Integer, default=900)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
