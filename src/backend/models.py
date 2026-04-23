# src/backend/models.py
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Connect to the Postgres container we just made
DATABASE_URL = "postgresql+pg8000://admin:password123@localhost:5432/vod_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True) # The UUID
    title = Column(String, index=True)
    status = Column(String, default="processing") # "processing", "ready", or "failed"
    hls_url = Column(String, nullable=True) # Where the frontend will find the stream
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# This creates the table inside Postgres automatically!
Base.metadata.create_all(bind=engine)