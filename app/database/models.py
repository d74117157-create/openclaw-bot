"""OpenClaw Empire — Database Models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.logger import logger

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False)
    goal = Column(Text, nullable=False)
    agent = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")
    result = Column(Text)
    source = Column(String(32), default="api")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(64), nullable=False)
    action = Column(String(128), nullable=False)
    details = Column(Text)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RevenueRecord(Base):
    __tablename__ = "revenue_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stream = Column(String(64), nullable=False)
    amount = Column(Float, default=0.0)
    source = Column(String(256))
    month_key = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(64), unique=True, nullable=False)
    content_type = Column(String(32), nullable=False)
    title = Column(String(512))
    platform = Column(String(64))
    url = Column(String(1024))
    revenue_potential = Column(Float, default=0.0)
    status = Column(String(32), default="created")
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(64), nullable=False)
    platform = Column(String(64))
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# Engine and session
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("[DB] Database initialized")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class FailureLog(Base):
    """Log of failed tasks and their causes."""
    __tablename__ = "failure_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False)
    agent_name = Column(String(64), nullable=False)
    error_type = Column(String(64), nullable=False)
    error_message = Column(Text)
    correction = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


class Correction(Base):
    """Store corrections to prevent repeating mistakes."""
    __tablename__ = "corrections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_task = Column(Text, nullable=False)
    failed_response = Column(Text)
    corrected_response = Column(Text)
    agent_name = Column(String(64), nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
