"""
SQLAlchemy database models for SiteGuard AI
Adapted for MySQL/Aurora compatibility
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """User model linked to Microsoft account"""
    __tablename__ = "users"
    
    # MySQL uses CHAR(36) for UUIDs instead of native UUID type
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    microsoft_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    role = Column(String(50), default="Viewer")  # Admin, Safety_Officer, Viewer
    profile_picture_url = Column(Text)
    organization = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    detection_history = relationship("DetectionHistory", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Report(Base):
    """Safety report model"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)
    location = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    format = Column(String(50))
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    violations = relationship("Violation", back_populates="report", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_reports_timestamp_location', 'timestamp', 'location'),
        Index('idx_reports_user_timestamp', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Report(id={self.id}, report_id={self.report_id}, location={self.location})>"


class Violation(Base):
    """PPE violation model"""
    __tablename__ = "violations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    violation_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    description = Column(Text)
    osha_standard = Column(String(50))
    confidence = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("Report", back_populates="violations")
    
    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_violations_type_timestamp', 'violation_type', 'timestamp'),
        Index('idx_violations_location_timestamp', 'location', 'timestamp'),
        Index('idx_violations_report', 'report_id'),
    )
    
    def __repr__(self):
        return f"<Violation(id={self.id}, type={self.violation_type}, severity={self.severity})>"


class DetectionHistory(Base):
    """Detection history for analytics"""
    __tablename__ = "detection_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_path = Column(String(500))
    detection_count = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    inference_time_ms = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="detection_history")
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_detection_history_timestamp', 'timestamp'),
        Index('idx_detection_history_user_timestamp', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<DetectionHistory(id={self.id}, detections={self.detection_count}, violations={self.violation_count})>"
