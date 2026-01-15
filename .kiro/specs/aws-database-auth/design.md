# Design Document: AWS Database & Microsoft SSO Integration

## Overview

This design document specifies the technical implementation for integrating AWS RDS PostgreSQL database and Microsoft Azure AD B2C authentication into the SiteGuard AI system. The implementation transforms the current stateless application into an enterprise-grade system with persistent data storage, user authentication, and role-based access control.

**Key Design Decisions:**
- **Database**: AWS RDS PostgreSQL with SQLAlchemy ORM for type-safe database operations
- **Authentication**: Microsoft Azure AD B2C with OAuth 2.0 / OpenID Connect for enterprise SSO
- **Architecture**: Hybrid cloud (AWS for database, Azure for authentication)
- **Migration Strategy**: Alembic for version-controlled schema changes
- **Session Management**: JWT tokens from Microsoft with server-side validation
- **Cost Optimization**: Free tier compliance for both AWS and Azure

**Design Philosophy:**
- Minimal code changes to existing system
- Backward compatibility during migration
- Security-first approach
- Demo-ready with easy teardown

---

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Web Browser                    API Client                      │
│  ┌──────────────┐              ┌──────────────┐                │
│  │  Streamlit   │              │  REST API    │                │
│  │  Dashboard   │              │  Consumer    │                │
│  └──────┬───────┘              └──────┬───────┘                │
│         │                             │                         │
└─────────┼─────────────────────────────┼─────────────────────────┘
          │                             │
          │ HTTPS                       │ HTTPS + JWT
          │                             │
┌─────────▼─────────────────────────────▼─────────────────────────┐
│                    APPLICATION LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Streamlit Frontend (Port 8501)            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │    │
│  │  │ Auth Module  │  │  Dashboard   │  │  Analytics  │ │    │
│  │  │ - Login UI   │  │  - Reports   │  │  - Charts   │ │    │
│  │  │ - Session    │  │  - History   │  │  - Trends   │ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │    │
│  └─────────┼──────────────────┼──────────────────┼────────┘    │
│            │                  │                  │              │
│            │                  │                  │              │
│  ┌─────────▼──────────────────▼──────────────────▼────────┐    │
│  │              FastAPI Backend (Port 8000)              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │    │
│  │  │ Auth         │  │  Detection   │  │  Database   │ │    │
│  │  │ Middleware   │  │  Service     │  │  Service    │ │    │
│  │  │ - JWT Verify │  │  - YOLOv8    │  │  - CRUD     │ │    │
│  │  │ - RBAC       │  │  - LLM       │  │  - Queries  │ │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │    │
│  └─────────┼──────────────────┼──────────────────┼────────┘    │
│            │                  │                  │              │
└────────────┼──────────────────┼──────────────────┼──────────────┘
             │                  │                  │
             │                  │                  │
┌────────────▼──────────────────┼──────────────────▼──────────────┐
│                    EXTERNAL SERVICES                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────┐      ┌─────────────────────────┐  │
│  │   Microsoft Azure       │      │      AWS Services       │  │
│  │   ─────────────────     │      │   ─────────────────     │  │
│  │                         │      │                         │  │
│  │  Azure AD B2C           │      │  RDS PostgreSQL         │  │
│  │  ┌───────────────────┐ │      │  ┌───────────────────┐ │  │
│  │  │ OAuth 2.0 Server  │ │      │  │  Database Engine  │ │  │
│  │  │ - Authorization   │ │      │  │  - PostgreSQL 15  │ │  │
│  │  │ - Token Endpoint  │ │      │  │  - db.t3.micro    │ │  │
│  │  │ - User Info       │ │      │  │  - 20GB Storage   │ │  │
│  │  └───────────────────┘ │      │  └───────────────────┘ │  │
│  │                         │      │                         │  │
│  │  User Directory         │      │  Tables:                │  │
│  │  - Profiles             │      │  - users                │  │
│  │  - Organizations        │      │  - reports              │  │
│  │  - MFA Settings         │      │  - violations           │  │
│  │                         │      │  - detection_history    │  │
│  └─────────────────────────┘      └─────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Action → Streamlit UI → FastAPI Backend → Database/Auth Service → Response
     │              │               │                    │              │
     │              │               │                    │              │
     ▼              ▼               ▼                    ▼              ▼
  Click         Validate        Check JWT          Query DB        Return
  Button        Session         Token              Execute         Data
                                                   Operation
```

---

## Components and Interfaces

### 1. Database Layer

#### 1.1 SQLAlchemy Models

**File**: `app/core/database/models.py`

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model linked to Microsoft account"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    microsoft_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255))
    role = Column(String(50), default="Viewer")  # Admin, Safety_Officer, Viewer
    profile_picture_url = Column(Text)
    organization = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    reports = relationship("Report", back_populates="user")
    detection_history = relationship("DetectionHistory", back_populates="user")

class Report(Base):
    """Safety report model"""
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    text = Column(Text, nullable=False)
    location = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    format = Column(String(50))
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    violations = relationship("Violation", back_populates="report", cascade="all, delete-orphan")

class Violation(Base):
    """PPE violation model"""
    __tablename__ = "violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    violation_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False)
    description = Column(Text)
    osha_standard = Column(String(50))
    confidence = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("Report", back_populates="violations")

class DetectionHistory(Base):
    """Detection history for analytics"""
    __tablename__ = "detection_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_path = Column(String(500))
    detection_count = Column(Integer, default=0)
    violation_count = Column(Integer, default=0)
    inference_time_ms = Column(Float)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="detection_history")
```

#### 1.2 Database Connection Manager

**File**: `app/core/database/connection.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections with connection pooling"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False  # Set to True for SQL logging
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables (for initial setup)"""
        from app.core.database.models import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

def get_db() -> Session:
    """Dependency for FastAPI routes"""
    with db_manager.get_session() as session:
        yield session
```


#### 1.3 Database Service Layer

**File**: `app/core/database/service.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.core.database.models import User, Report, Violation, DetectionHistory
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    # User Operations
    def get_or_create_user(self, microsoft_user_id: str, email: str, name: str, 
                          profile_picture_url: Optional[str] = None,
                          organization: Optional[str] = None) -> User:
        """Get existing user or create new one"""
        user = self.session.query(User).filter(
            User.microsoft_user_id == microsoft_user_id
        ).first()
        
        if user:
            # Update last login
            user.last_login = datetime.utcnow()
            user.profile_picture_url = profile_picture_url
            user.organization = organization
            self.session.commit()
        else:
            # Create new user with default Viewer role
            user = User(
                microsoft_user_id=microsoft_user_id,
                email=email,
                name=name,
                role="Viewer",
                profile_picture_url=profile_picture_url,
                organization=organization,
                last_login=datetime.utcnow()
            )
            self.session.add(user)
            self.session.commit()
            logger.info(f"Created new user: {email}")
        
        return user
    
    def update_user_role(self, user_id: str, role: str) -> User:
        """Update user role (Admin only)"""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if role not in ["Admin", "Safety_Officer", "Viewer"]:
            raise ValueError(f"Invalid role: {role}")
        
        user.role = role
        self.session.commit()
        logger.info(f"Updated user {user.email} role to {role}")
        return user
    
    # Report Operations
    def create_report(self, report_data: Dict[str, Any], user_id: str) -> Report:
        """Create a new safety report"""
        report = Report(
            report_id=report_data["report_id"],
            title=report_data["title"],
            text=report_data["text"],
            location=report_data["location"],
            timestamp=report_data["timestamp"],
            user_id=user_id,
            format=report_data.get("format", "text"),
            metadata_json=report_data.get("metadata", {})
        )
        self.session.add(report)
        self.session.commit()
        logger.info(f"Created report: {report.report_id}")
        return report
    
    def get_reports(self, user_id: Optional[str] = None, 
                   location: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 100, offset: int = 0) -> List[Report]:
        """Get reports with optional filters"""
        query = self.session.query(Report)
        
        if user_id:
            query = query.filter(Report.user_id == user_id)
        if location:
            query = query.filter(Report.location == location)
        if start_date:
            query = query.filter(Report.timestamp >= start_date)
        if end_date:
            query = query.filter(Report.timestamp <= end_date)
        
        return query.order_by(Report.timestamp.desc()).limit(limit).offset(offset).all()
    
    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Get a specific report"""
        return self.session.query(Report).filter(Report.report_id == report_id).first()
    
    # Violation Operations
    def create_violation(self, violation_data: Dict[str, Any], report_id: str) -> Violation:
        """Create a violation linked to a report"""
        violation = Violation(
            violation_type=violation_data["violation_type"],
            severity=violation_data["severity"],
            description=violation_data.get("description"),
            osha_standard=violation_data.get("osha_standard"),
            confidence=violation_data.get("confidence"),
            timestamp=violation_data["timestamp"],
            location=violation_data["location"],
            report_id=report_id
        )
        self.session.add(violation)
        self.session.commit()
        return violation
    
    def get_violations(self, location: Optional[str] = None,
                      violation_type: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> List[Violation]:
        """Get violations with optional filters"""
        query = self.session.query(Violation)
        
        if location:
            query = query.filter(Violation.location == location)
        if violation_type:
            query = query.filter(Violation.violation_type == violation_type)
        if start_date:
            query = query.filter(Violation.timestamp >= start_date)
        if end_date:
            query = query.filter(Violation.timestamp <= end_date)
        
        return query.order_by(Violation.timestamp.desc()).limit(limit).all()
    
    # Detection History Operations
    def create_detection_history(self, detection_data: Dict[str, Any], user_id: str) -> DetectionHistory:
        """Record a detection event"""
        history = DetectionHistory(
            image_path=detection_data.get("image_path"),
            detection_count=detection_data.get("detection_count", 0),
            violation_count=detection_data.get("violation_count", 0),
            inference_time_ms=detection_data.get("inference_time_ms"),
            timestamp=detection_data["timestamp"],
            user_id=user_id
        )
        self.session.add(history)
        self.session.commit()
        return history
    
    # Analytics Queries
    def get_violation_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get violation trends over time"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.date(Violation.timestamp).label("date"),
            func.count(Violation.id).label("count")
        ).filter(
            Violation.timestamp >= start_date
        ).group_by(
            func.date(Violation.timestamp)
        ).order_by(
            func.date(Violation.timestamp)
        ).all()
        
        return [{"date": str(r.date), "count": r.count} for r in results]
    
    def get_top_violation_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common violation types"""
        results = self.session.query(
            Violation.violation_type,
            func.count(Violation.id).label("count")
        ).group_by(
            Violation.violation_type
        ).order_by(
            func.count(Violation.id).desc()
        ).limit(limit).all()
        
        return [{"violation_type": r.violation_type, "count": r.count} for r in results]
    
    def get_location_analytics(self) -> List[Dict[str, Any]]:
        """Get violation statistics by location"""
        results = self.session.query(
            Violation.location,
            func.count(Violation.id).label("total_violations"),
            func.avg(Violation.confidence).label("avg_confidence")
        ).group_by(
            Violation.location
        ).order_by(
            func.count(Violation.id).desc()
        ).all()
        
        return [{
            "location": r.location,
            "total_violations": r.total_violations,
            "avg_confidence": float(r.avg_confidence) if r.avg_confidence else 0
        } for r in results]
    
    def get_compliance_rate(self, days: int = 30) -> Dict[str, Any]:
        """Calculate compliance rate"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_detections = self.session.query(
            func.sum(DetectionHistory.detection_count)
        ).filter(
            DetectionHistory.timestamp >= start_date
        ).scalar() or 0
        
        total_violations = self.session.query(
            func.count(Violation.id)
        ).filter(
            Violation.timestamp >= start_date
        ).scalar() or 0
        
        compliance_rate = 0
        if total_detections > 0:
            compliance_rate = ((total_detections - total_violations) / total_detections) * 100
        
        return {
            "total_detections": total_detections,
            "total_violations": total_violations,
            "compliance_rate": round(compliance_rate, 2)
        }
```

---

### 2. Authentication Layer

#### 2.1 Microsoft Azure AD B2C Configuration

**File**: `app/core/auth/config.py`

```python
import os
from typing import Dict, Any

class AzureADConfig:
    """Azure AD B2C configuration"""
    
    # Azure AD B2C Settings
    TENANT_ID = os.getenv("AZURE_AD_TENANT_ID")
    CLIENT_ID = os.getenv("AZURE_AD_CLIENT_ID")
    CLIENT_SECRET = os.getenv("AZURE_AD_CLIENT_SECRET")
    
    # Authority URL (login endpoint)
    AUTHORITY = os.getenv(
        "AZURE_AD_AUTHORITY",
        f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    
    # Redirect URI (where Microsoft sends user after login)
    REDIRECT_URI = os.getenv("AZURE_AD_REDIRECT_URI", "http://localhost:8501/callback")
    
    # Scopes (what permissions we request)
    SCOPES = ["User.Read", "openid", "profile", "email"]
    
    # Endpoints
    AUTHORIZATION_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
    TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"
    USERINFO_ENDPOINT = "https://graph.microsoft.com/v1.0/me"
    
    @classmethod
    def validate(cls):
        """Validate all required configuration is present"""
        required = ["TENANT_ID", "CLIENT_ID", "CLIENT_SECRET"]
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing Azure AD configuration: {', '.join(missing)}")
    
    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        """Generate Microsoft login URL"""
        params = {
            "client_id": cls.CLIENT_ID,
            "response_type": "code",
            "redirect_uri": cls.REDIRECT_URI,
            "scope": " ".join(cls.SCOPES),
            "state": state,
            "response_mode": "query"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{cls.AUTHORIZATION_ENDPOINT}?{query_string}"
```

#### 2.2 OAuth Flow Handler

**File**: `app/core/auth/oauth.py`

```python
import msal
import requests
from typing import Dict, Any, Optional
from app.core.auth.config import AzureADConfig
import logging

logger = logging.getLogger(__name__)

class MicrosoftOAuthHandler:
    """Handles Microsoft OAuth 2.0 flow"""
    
    def __init__(self):
        AzureADConfig.validate()
        
        # Create MSAL confidential client
        self.client = msal.ConfidentialClientApplication(
            client_id=AzureADConfig.CLIENT_ID,
            client_credential=AzureADConfig.CLIENT_SECRET,
            authority=AzureADConfig.AUTHORITY
        )
    
    def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL for user to visit"""
        auth_url = self.client.get_authorization_request_url(
            scopes=AzureADConfig.SCOPES,
            state=state,
            redirect_uri=AzureADConfig.REDIRECT_URI
        )
        return auth_url
    
    def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            result = self.client.acquire_token_by_authorization_code(
                code=authorization_code,
                scopes=AzureADConfig.SCOPES,
                redirect_uri=AzureADConfig.REDIRECT_URI
            )
            
            if "error" in result:
                logger.error(f"Token exchange error: {result.get('error_description')}")
                raise ValueError(f"Token exchange failed: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Token exchange exception: {e}")
            raise
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph API"""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            # Get basic user info
            response = requests.get(AzureADConfig.USERINFO_ENDPOINT, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            
            # Get profile picture
            photo_url = None
            try:
                photo_response = requests.get(
                    "https://graph.microsoft.com/v1.0/me/photo/$value",
                    headers=headers
                )
                if photo_response.status_code == 200:
                    # In production, save to S3 and store URL
                    # For demo, we'll use Microsoft's photo endpoint
                    photo_url = "https://graph.microsoft.com/v1.0/me/photo/$value"
            except:
                pass  # Photo is optional
            
            return {
                "microsoft_user_id": user_info.get("id"),
                "email": user_info.get("mail") or user_info.get("userPrincipalName"),
                "name": user_info.get("displayName"),
                "profile_picture_url": photo_url,
                "organization": user_info.get("companyName")
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token"""
        try:
            result = self.client.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=AzureADConfig.SCOPES
            )
            
            if "error" in result:
                raise ValueError(f"Token refresh failed: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Token refresh exception: {e}")
            raise
```


#### 2.3 JWT Token Validation

**File**: `app/core/auth/jwt_handler.py`

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class JWTHandler:
    """Handles JWT token validation and creation"""
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    
    @classmethod
    def create_access_token(cls, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise ValueError("Invalid token")
    
    @classmethod
    def verify_microsoft_token(cls, token: str) -> Dict[str, Any]:
        """Verify a Microsoft-issued JWT token"""
        # For Microsoft tokens, we need to verify against Microsoft's public keys
        # This is a simplified version - in production, fetch and cache Microsoft's JWKS
        try:
            # Decode without verification for demo (Microsoft already verified it)
            # In production, verify signature using Microsoft's public keys
            payload = jwt.decode(
                token,
                options={"verify_signature": False}  # ONLY for demo
            )
            
            # Verify token hasn't expired
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                if datetime.utcnow().timestamp() > exp_timestamp:
                    raise ValueError("Token has expired")
            
            return payload
        except Exception as e:
            logger.error(f"Microsoft token verification failed: {e}")
            raise ValueError("Invalid Microsoft token")
```

#### 2.4 Authentication Middleware

**File**: `app/core/auth/middleware.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.auth.jwt_handler import JWTHandler
from app.core.database.connection import get_db
from app.core.database.models import User
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> User:
        """Get current authenticated user from JWT token"""
        token = credentials.credentials
        
        try:
            # Verify token
            payload = JWTHandler.verify_token(token)
            microsoft_user_id = payload.get("microsoft_user_id")
            
            if not microsoft_user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            user = db.query(User).filter(
                User.microsoft_user_id == microsoft_user_id
            ).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
        
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    @staticmethod
    def require_role(required_role: str):
        """Decorator to require specific role"""
        def role_checker(user: User = Depends(AuthMiddleware.get_current_user)) -> User:
            role_hierarchy = {
                "Viewer": 1,
                "Safety_Officer": 2,
                "Admin": 3
            }
            
            user_level = role_hierarchy.get(user.role, 0)
            required_level = role_hierarchy.get(required_role, 999)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role}"
                )
            
            return user
        
        return role_checker
    
    @staticmethod
    def optional_auth(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[User]:
        """Optional authentication - returns None if not authenticated"""
        if not credentials:
            return None
        
        try:
            return AuthMiddleware.get_current_user(credentials, db)
        except:
            return None
```

---

### 3. API Integration

#### 3.1 Authentication Endpoints

**File**: `app/api/auth_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.auth.oauth import MicrosoftOAuthHandler
from app.core.auth.jwt_handler import JWTHandler
from app.core.database.connection import get_db
from app.core.database.service import DatabaseService
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory state storage (use Redis in production)
auth_states = {}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

@router.get("/login")
async def login():
    """Initiate Microsoft OAuth login"""
    oauth_handler = MicrosoftOAuthHandler()
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    auth_states[state] = True
    
    # Get authorization URL
    auth_url = oauth_handler.get_authorization_url(state)
    
    return {"authorization_url": auth_url, "state": state}

@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle OAuth callback from Microsoft"""
    
    # Verify state to prevent CSRF
    if state not in auth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Remove used state
    del auth_states[state]
    
    try:
        oauth_handler = MicrosoftOAuthHandler()
        
        # Exchange code for token
        token_result = oauth_handler.exchange_code_for_token(code)
        access_token = token_result["access_token"]
        
        # Get user info from Microsoft
        user_info = oauth_handler.get_user_info(access_token)
        
        # Create or update user in database
        db_service = DatabaseService(db)
        user = db_service.get_or_create_user(
            microsoft_user_id=user_info["microsoft_user_id"],
            email=user_info["email"],
            name=user_info["name"],
            profile_picture_url=user_info.get("profile_picture_url"),
            organization=user_info.get("organization")
        )
        
        # Create our own JWT token
        jwt_token = JWTHandler.create_access_token({
            "microsoft_user_id": user.microsoft_user_id,
            "email": user.email,
            "role": user.role
        })
        
        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=3600,
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_picture_url": user.profile_picture_url,
                "organization": user.organization
            }
        )
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/logout")
async def logout():
    """Logout user (client should delete token)"""
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_info(user: User = Depends(AuthMiddleware.get_current_user)):
    """Get current user information"""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_picture_url": user.profile_picture_url,
        "organization": user.organization,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
```

#### 3.2 Protected Report Endpoints

**File**: `app/api/report_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.auth.middleware import AuthMiddleware
from app.core.database.connection import get_db
from app.core.database.service import DatabaseService
from app.core.database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

class ReportCreate(BaseModel):
    report_id: str
    title: str
    text: str
    location: str
    timestamp: datetime
    format: Optional[str] = "text"
    metadata: Optional[dict] = {}

class ViolationCreate(BaseModel):
    violation_type: str
    severity: str
    description: Optional[str]
    osha_standard: Optional[str]
    confidence: Optional[float]
    timestamp: datetime
    location: str

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    report: ReportCreate,
    user: User = Depends(AuthMiddleware.require_role("Safety_Officer")),
    db: Session = Depends(get_db)
):
    """Create a new safety report (Safety Officer or Admin only)"""
    try:
        db_service = DatabaseService(db)
        created_report = db_service.create_report(
            report_data=report.dict(),
            user_id=str(user.id)
        )
        
        return {
            "id": str(created_report.id),
            "report_id": created_report.report_id,
            "message": "Report created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report"
        )

@router.get("/")
async def get_reports(
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get reports (all authenticated users)"""
    try:
        db_service = DatabaseService(db)
        reports = db_service.get_reports(
            location=location,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return [{
            "id": str(r.id),
            "report_id": r.report_id,
            "title": r.title,
            "location": r.location,
            "timestamp": r.timestamp.isoformat(),
            "user_email": r.user.email if r.user else None,
            "violation_count": len(r.violations)
        } for r in reports]
    except Exception as e:
        logger.error(f"Failed to get reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )

@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific report"""
    try:
        db_service = DatabaseService(db)
        report = db_service.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        return {
            "id": str(report.id),
            "report_id": report.report_id,
            "title": report.title,
            "text": report.text,
            "location": report.location,
            "timestamp": report.timestamp.isoformat(),
            "format": report.format,
            "metadata": report.metadata_json,
            "user": {
                "email": report.user.email,
                "name": report.user.name
            } if report.user else None,
            "violations": [{
                "violation_type": v.violation_type,
                "severity": v.severity,
                "description": v.description,
                "confidence": v.confidence
            } for v in report.violations]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )

@router.post("/{report_id}/violations", status_code=status.HTTP_201_CREATED)
async def add_violation(
    report_id: str,
    violation: ViolationCreate,
    user: User = Depends(AuthMiddleware.require_role("Safety_Officer")),
    db: Session = Depends(get_db)
):
    """Add a violation to a report"""
    try:
        db_service = DatabaseService(db)
        
        # Verify report exists
        report = db_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        created_violation = db_service.create_violation(
            violation_data=violation.dict(),
            report_id=str(report.id)
        )
        
        return {
            "id": str(created_violation.id),
            "message": "Violation added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add violation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add violation"
        )
```


#### 3.3 Analytics Endpoints

**File**: `app/api/analytics_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth.middleware import AuthMiddleware
from app.core.database.connection import get_db
from app.core.database.service import DatabaseService
from app.core.database.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/violation-trends")
async def get_violation_trends(
    days: int = 30,
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get violation trends over time"""
    try:
        db_service = DatabaseService(db)
        trends = db_service.get_violation_trends(days=days)
        return {"trends": trends}
    except Exception as e:
        logger.error(f"Failed to get violation trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trends"
        )

@router.get("/top-violations")
async def get_top_violations(
    limit: int = 10,
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get most common violation types"""
    try:
        db_service = DatabaseService(db)
        top_violations = db_service.get_top_violation_types(limit=limit)
        return {"top_violations": top_violations}
    except Exception as e:
        logger.error(f"Failed to get top violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top violations"
        )

@router.get("/location-analytics")
async def get_location_analytics(
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get violation statistics by location"""
    try:
        db_service = DatabaseService(db)
        location_stats = db_service.get_location_analytics()
        return {"location_analytics": location_stats}
    except Exception as e:
        logger.error(f"Failed to get location analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location analytics"
        )

@router.get("/compliance-rate")
async def get_compliance_rate(
    days: int = 30,
    user: User = Depends(AuthMiddleware.get_current_user),
    db: Session = Depends(get_db)
):
    """Get compliance rate"""
    try:
        db_service = DatabaseService(db)
        compliance = db_service.get_compliance_rate(days=days)
        return compliance
    except Exception as e:
        logger.error(f"Failed to get compliance rate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve compliance rate"
        )

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint (no auth required)"""
    from app.core.database.connection import db_manager
    
    db_healthy = db_manager.health_check()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected"
    }
```

---

### 4. Streamlit Integration

#### 4.1 Authentication Module

**File**: `app/web/auth_module.py`

```python
import streamlit as st
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class StreamlitAuth:
    """Handles authentication in Streamlit"""
    
    API_BASE_URL = "http://localhost:8000"
    
    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "user" not in st.session_state:
            st.session_state.user = None
        if "access_token" not in st.session_state:
            st.session_state.access_token = None
    
    @staticmethod
    def show_login_page():
        """Display login page with Microsoft sign-in"""
        st.title("🔐 SiteGuard AI - Login")
        st.markdown("### Enterprise Safety Monitoring System")
        
        st.info("👋 Please sign in with your Microsoft account to continue")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔑 Sign in with Microsoft", use_container_width=True, type="primary"):
                try:
                    # Get authorization URL from backend
                    response = requests.get(f"{StreamlitAuth.API_BASE_URL}/auth/login")
                    response.raise_for_status()
                    
                    data = response.json()
                    auth_url = data["authorization_url"]
                    state = data["state"]
                    
                    # Store state in session
                    st.session_state.oauth_state = state
                    
                    # Redirect to Microsoft login
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                    st.info("Redirecting to Microsoft login...")
                
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
                    logger.error(f"Login error: {e}")
        
        st.markdown("---")
        st.caption("🔒 Secure authentication powered by Microsoft Azure AD B2C")
    
    @staticmethod
    def handle_callback():
        """Handle OAuth callback"""
        query_params = st.query_params
        
        if "code" in query_params and "state" in query_params:
            code = query_params["code"]
            state = query_params["state"]
            
            try:
                # Exchange code for token
                response = requests.get(
                    f"{StreamlitAuth.API_BASE_URL}/auth/callback",
                    params={"code": code, "state": state}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Store in session
                st.session_state.authenticated = True
                st.session_state.access_token = data["access_token"]
                st.session_state.user = data["user"]
                
                # Clear query params
                st.query_params.clear()
                
                # Rerun to show main app
                st.rerun()
            
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")
                logger.error(f"Callback error: {e}")
                st.session_state.authenticated = False
    
    @staticmethod
    def logout():
        """Logout user"""
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.access_token = None
        st.rerun()
    
    @staticmethod
    def get_auth_headers() -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if st.session_state.access_token:
            return {"Authorization": f"Bearer {st.session_state.access_token}"}
        return {}
    
    @staticmethod
    def show_user_info():
        """Display user info in sidebar"""
        if st.session_state.user:
            user = st.session_state.user
            
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 User Profile")
                
                # Show profile picture if available
                if user.get("profile_picture_url"):
                    st.image(user["profile_picture_url"], width=80)
                
                st.markdown(f"**{user['name']}**")
                st.caption(user['email'])
                
                # Show role badge
                role = user['role']
                role_colors = {
                    "Admin": "🔴",
                    "Safety_Officer": "🟡",
                    "Viewer": "🟢"
                }
                st.markdown(f"{role_colors.get(role, '⚪')} Role: **{role}**")
                
                # Show organization if available
                if user.get("organization"):
                    st.caption(f"🏢 {user['organization']}")
                
                # Logout button
                if st.button("🚪 Logout", use_container_width=True):
                    StreamlitAuth.logout()
    
    @staticmethod
    def require_auth():
        """Decorator to require authentication"""
        StreamlitAuth.initialize_session()
        StreamlitAuth.handle_callback()
        
        if not st.session_state.authenticated:
            StreamlitAuth.show_login_page()
            st.stop()
        
        StreamlitAuth.show_user_info()
    
    @staticmethod
    def require_role(required_role: str):
        """Check if user has required role"""
        StreamlitAuth.require_auth()
        
        user = st.session_state.user
        role_hierarchy = {
            "Viewer": 1,
            "Safety_Officer": 2,
            "Admin": 3
        }
        
        user_level = role_hierarchy.get(user["role"], 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            st.error(f"⛔ Access Denied: This feature requires {required_role} role")
            st.stop()
```

#### 4.2 Updated Streamlit Main App

**File**: `app/web/streamlit_app_enhanced.py` (modifications)

```python
import streamlit as st
from app.web.auth_module import StreamlitAuth
import requests

# Configure page
st.set_page_config(
    page_title="SiteGuard AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Require authentication
StreamlitAuth.require_auth()

# Get auth headers for API calls
auth_headers = StreamlitAuth.get_auth_headers()

# Main app content
def main():
    st.title("🏗️ SiteGuard AI - Safety Monitoring Dashboard")
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio(
            "Select Page",
            ["Dashboard", "Reports", "Analytics", "Settings"]
        )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Reports":
        show_reports()
    elif page == "Analytics":
        show_analytics()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Main dashboard page"""
    st.header("📊 Dashboard")
    
    # Fetch recent reports from API
    try:
        response = requests.get(
            f"{StreamlitAuth.API_BASE_URL}/reports",
            headers=auth_headers,
            params={"limit": 10}
        )
        response.raise_for_status()
        reports = response.json()
        
        st.metric("Total Reports", len(reports))
        
        # Display reports
        for report in reports:
            with st.expander(f"📄 {report['title']}"):
                st.write(f"**Location:** {report['location']}")
                st.write(f"**Time:** {report['timestamp']}")
                st.write(f"**Violations:** {report['violation_count']}")
    
    except Exception as e:
        st.error(f"Failed to load reports: {str(e)}")

def show_reports():
    """Reports page - requires Safety Officer role"""
    StreamlitAuth.require_role("Safety_Officer")
    
    st.header("📝 Reports")
    st.write("Generate and view safety reports")
    
    # Report generation form
    with st.form("generate_report"):
        location = st.text_input("Location")
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
        
        if st.form_submit_button("Generate Report"):
            if uploaded_file and location:
                # Process image and generate report
                # (existing detection logic)
                st.success("Report generated successfully!")
            else:
                st.warning("Please provide location and image")

def show_analytics():
    """Analytics page"""
    st.header("📈 Analytics")
    
    # Fetch analytics data
    try:
        # Violation trends
        response = requests.get(
            f"{StreamlitAuth.API_BASE_URL}/analytics/violation-trends",
            headers=auth_headers,
            params={"days": 30}
        )
        response.raise_for_status()
        trends = response.json()["trends"]
        
        st.subheader("Violation Trends (Last 30 Days)")
        st.line_chart(trends)
        
        # Compliance rate
        response = requests.get(
            f"{StreamlitAuth.API_BASE_URL}/analytics/compliance-rate",
            headers=auth_headers
        )
        response.raise_for_status()
        compliance = response.json()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Detections", compliance["total_detections"])
        col2.metric("Total Violations", compliance["total_violations"])
        col3.metric("Compliance Rate", f"{compliance['compliance_rate']}%")
    
    except Exception as e:
        st.error(f"Failed to load analytics: {str(e)}")

def show_settings():
    """Settings page - Admin only"""
    StreamlitAuth.require_role("Admin")
    
    st.header("⚙️ Settings")
    st.write("System configuration (Admin only)")
    
    # Admin settings
    st.subheader("User Management")
    st.info("User role management coming soon")

if __name__ == "__main__":
    main()
```

---

## Data Models

### Database Schema

The complete database schema is defined in the SQLAlchemy models above. Here's a visual representation:

```
┌─────────────────────────────────────────────────────────────┐
│                         USERS TABLE                          │
├─────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                               │
│ microsoft_user_id (VARCHAR, UNIQUE, INDEXED)                │
│ email (VARCHAR, INDEXED)                                    │
│ name (VARCHAR)                                              │
│ role (VARCHAR) - Admin/Safety_Officer/Viewer                │
│ profile_picture_url (TEXT)                                  │
│ organization (VARCHAR)                                      │
│ created_at (TIMESTAMP)                                      │
│ last_login (TIMESTAMP)                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        REPORTS TABLE                         │
├─────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                               │
│ report_id (VARCHAR, UNIQUE)                                 │
│ title (VARCHAR)                                             │
│ text (TEXT)                                                 │
│ location (VARCHAR, INDEXED)                                 │
│ timestamp (TIMESTAMP, INDEXED)                              │
│ user_id (UUID, FK → users.id)                              │
│ format (VARCHAR)                                            │
│ metadata_json (JSONB)                                       │
│ created_at (TIMESTAMP)                                      │
│ updated_at (TIMESTAMP)                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      VIOLATIONS TABLE                        │
├─────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                               │
│ violation_type (VARCHAR, INDEXED)                           │
│ severity (VARCHAR)                                          │
│ description (TEXT)                                          │
│ osha_standard (VARCHAR)                                     │
│ confidence (FLOAT)                                          │
│ timestamp (TIMESTAMP, INDEXED)                              │
│ location (VARCHAR, INDEXED)                                 │
│ report_id (UUID, FK → reports.id, CASCADE DELETE)          │
│ created_at (TIMESTAMP)                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   DETECTION_HISTORY TABLE                    │
├─────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                               │
│ image_path (VARCHAR)                                        │
│ detection_count (INTEGER)                                   │
│ violation_count (INTEGER)                                   │
│ inference_time_ms (FLOAT)                                   │
│ timestamp (TIMESTAMP, INDEXED)                              │
│ user_id (UUID, FK → users.id)                              │
│ created_at (TIMESTAMP)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Indexes

Performance-critical indexes:
- `users.microsoft_user_id` - Fast user lookup during authentication
- `users.email` - Email-based queries
- `reports.timestamp` - Time-based report queries
- `reports.location` - Location-based filtering
- `violations.violation_type` - Violation type analytics
- `violations.timestamp` - Time-based violation queries
- `violations.location` - Location-based analytics
- `detection_history.timestamp` - Historical analytics

---


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: User Authentication Round Trip

*For any* valid Microsoft user credentials, authenticating through the OAuth flow should result in a user record in the database with matching Microsoft user ID and email.

**Validates: Requirements 2.3, 2.4, 2.10**

### Property 2: Database Connection Persistence

*For any* database operation, if the connection is healthy before the operation, the operation should either succeed or fail with a clear error, and the connection should remain healthy afterward.

**Validates: Requirements 1.1, 1.5**

### Property 3: Report Storage Completeness

*For any* generated report with violations, storing the report in the database should result in all violations being retrievable through the report's foreign key relationship.

**Validates: Requirements 1.2, 1.3**

### Property 4: JWT Token Validation

*For any* JWT token created by the system, verifying the token before expiration should return the original payload data without modification.

**Validates: Requirements 2.6, 2.7**

### Property 5: Role-Based Access Control Enforcement

*For any* API endpoint protected by role requirements, a user with insufficient role level should receive a 403 Forbidden error, while a user with sufficient role level should be allowed to proceed.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**

### Property 6: Database Query Pagination Consistency

*For any* paginated query with limit N and offset M, the union of results from (limit=N, offset=0) and (limit=N, offset=N) should equal the results from (limit=2N, offset=0) when ordered consistently.

**Validates: Requirements 12.3**

### Property 7: Analytics Aggregation Accuracy

*For any* time period, the sum of daily violation counts from the trends query should equal the total violation count from the compliance rate query for the same period.

**Validates: Requirements 10.1, 10.2**

### Property 8: Foreign Key Cascade Deletion

*For any* report with associated violations, deleting the report should result in all associated violations being automatically deleted from the database.

**Validates: Requirements 4.5**

### Property 9: Session State Consistency

*For any* authenticated Streamlit session, the access token in session state should be valid and correspond to the user information displayed in the sidebar.

**Validates: Requirements 6.4, 6.6**

### Property 10: OAuth State CSRF Protection

*For any* OAuth callback, if the state parameter doesn't match a previously generated state, the authentication should fail with a 400 Bad Request error.

**Validates: Requirements 2.2, 2.3**

### Property 11: Database Index Performance

*For any* indexed column query (timestamp, location, violation_type), the query execution time should be significantly faster than a full table scan on the same data.

**Validates: Requirements 1.7, 12.1**

### Property 12: User Role Default Assignment

*For any* new user created through Microsoft authentication, the user should be assigned the "Viewer" role by default.

**Validates: Requirements 3.8**

### Property 13: Connection Pool Exhaustion Handling

*For any* scenario where all database connections are in use, new requests should either wait for an available connection or return an appropriate error, never causing a system crash.

**Validates: Requirements 12.2, 12.5**

### Property 14: Microsoft Token Expiration Handling

*For any* expired JWT token from Microsoft, API requests using that token should return a 401 Unauthorized error and prompt for re-authentication.

**Validates: Requirements 2.7, 6.8**

### Property 15: Analytics Date Range Filtering

*For any* analytics query with start_date and end_date parameters, all returned results should have timestamps within the specified range (inclusive).

**Validates: Requirements 10.6**

---

## Error Handling

### Error Categories

#### 1. Authentication Errors

**OAuth Flow Errors:**
```python
class AuthenticationError(Exception):
    """Base authentication error"""
    pass

class InvalidStateError(AuthenticationError):
    """OAuth state mismatch (CSRF protection)"""
    http_status = 400
    message = "Invalid state parameter"

class TokenExchangeError(AuthenticationError):
    """Failed to exchange authorization code for token"""
    http_status = 500
    message = "Token exchange failed"

class InvalidTokenError(AuthenticationError):
    """JWT token validation failed"""
    http_status = 401
    message = "Invalid or expired token"

class InsufficientPermissionsError(AuthenticationError):
    """User lacks required role"""
    http_status = 403
    message = "Insufficient permissions"
```

**Error Handling Strategy:**
- Log all authentication errors with user context
- Return user-friendly error messages (no sensitive details)
- Redirect to login page on token expiration
- Implement exponential backoff for token refresh attempts

#### 2. Database Errors

**Connection Errors:**
```python
class DatabaseError(Exception):
    """Base database error"""
    pass

class ConnectionError(DatabaseError):
    """Database connection failed"""
    http_status = 503
    message = "Database temporarily unavailable"
    retry_after = 30  # seconds

class QueryTimeoutError(DatabaseError):
    """Query exceeded timeout"""
    http_status = 504
    message = "Request timeout"

class IntegrityError(DatabaseError):
    """Foreign key or unique constraint violation"""
    http_status = 409
    message = "Data integrity violation"
```

**Error Handling Strategy:**
- Implement automatic retry with exponential backoff (max 3 attempts)
- Use connection pooling to prevent connection exhaustion
- Log slow queries (>1 second) for optimization
- Graceful degradation: show cached data if database unavailable

#### 3. API Errors

**Request Validation Errors:**
```python
class ValidationError(Exception):
    """Request validation failed"""
    http_status = 422
    
class NotFoundError(Exception):
    """Resource not found"""
    http_status = 404

class RateLimitError(Exception):
    """Too many requests"""
    http_status = 429
    retry_after = 60
```

**Error Response Format:**
```json
{
    "error": {
        "code": "INVALID_TOKEN",
        "message": "Your session has expired. Please log in again.",
        "details": null,
        "timestamp": "2026-01-14T12:00:00Z"
    }
}
```

### Error Logging

**Structured Logging:**
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    """Structured JSON logging for error tracking"""
    
    @staticmethod
    def log_error(error: Exception, context: dict):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context,
            "stack_trace": traceback.format_exc()
        }
        
        logging.error(json.dumps(log_entry))
```

**Context to Include:**
- User ID (if authenticated)
- Request ID (for tracing)
- Endpoint/function name
- Input parameters (sanitized)
- Database query (if applicable)

### Graceful Degradation

**Fallback Strategies:**

1. **Database Unavailable:**
   - Show cached analytics data
   - Allow read-only mode with warning banner
   - Queue write operations for retry

2. **Microsoft OAuth Down:**
   - Show maintenance message
   - Allow API key authentication as backup
   - Cache user sessions longer

3. **Slow Queries:**
   - Implement query timeout (5 seconds)
   - Return partial results with warning
   - Suggest narrower date range

---

## Testing Strategy

### Testing Approach

We will implement a dual testing strategy combining unit tests for specific scenarios and property-based tests for comprehensive coverage.

**Testing Pyramid:**
```
        ┌─────────────────┐
        │  Integration    │  ← 20% (E2E flows)
        │     Tests       │
        ├─────────────────┤
        │  Property-Based │  ← 30% (Universal properties)
        │     Tests       │
        ├─────────────────┤
        │   Unit Tests    │  ← 50% (Specific cases)
        └─────────────────┘
```

### 1. Unit Tests

**Purpose:** Test specific examples, edge cases, and error conditions

**Framework:** pytest

**Coverage Areas:**

#### Database Tests
```python
# tests/test_database.py

def test_create_user_with_valid_data():
    """Test creating a user with valid Microsoft credentials"""
    # Specific example: known good data
    user = db_service.get_or_create_user(
        microsoft_user_id="12345",
        email="test@example.com",
        name="Test User"
    )
    assert user.email == "test@example.com"
    assert user.role == "Viewer"  # Default role

def test_create_user_with_missing_email():
    """Test error handling for missing email"""
    with pytest.raises(ValueError):
        db_service.get_or_create_user(
            microsoft_user_id="12345",
            email=None,
            name="Test User"
        )

def test_report_cascade_delete():
    """Test that deleting a report deletes associated violations"""
    # Create report with violations
    report = create_test_report()
    violation = create_test_violation(report_id=report.id)
    
    # Delete report
    db.delete(report)
    db.commit()
    
    # Verify violation is gone
    assert db.query(Violation).filter_by(id=violation.id).first() is None
```

#### Authentication Tests
```python
# tests/test_auth.py

def test_jwt_token_creation_and_verification():
    """Test JWT token round trip"""
    payload = {"microsoft_user_id": "12345", "email": "test@example.com"}
    token = JWTHandler.create_access_token(payload)
    decoded = JWTHandler.verify_token(token)
    
    assert decoded["microsoft_user_id"] == "12345"
    assert decoded["email"] == "test@example.com"

def test_expired_token_rejection():
    """Test that expired tokens are rejected"""
    # Create token that expires immediately
    payload = {"microsoft_user_id": "12345"}
    token = JWTHandler.create_access_token(payload, expires_delta=timedelta(seconds=-1))
    
    with pytest.raises(ValueError, match="expired"):
        JWTHandler.verify_token(token)

def test_role_based_access_control():
    """Test RBAC enforcement"""
    viewer = User(role="Viewer")
    admin = User(role="Admin")
    
    # Viewer should be denied
    with pytest.raises(HTTPException) as exc:
        AuthMiddleware.require_role("Admin")(viewer)
    assert exc.value.status_code == 403
    
    # Admin should be allowed
    result = AuthMiddleware.require_role("Admin")(admin)
    assert result == admin
```

#### API Tests
```python
# tests/test_api.py

def test_create_report_requires_authentication():
    """Test that creating a report requires auth"""
    client = TestClient(app)
    response = client.post("/reports/", json={"title": "Test"})
    assert response.status_code == 401

def test_create_report_requires_safety_officer_role():
    """Test that creating a report requires Safety Officer role"""
    viewer_token = create_test_token(role="Viewer")
    client = TestClient(app)
    
    response = client.post(
        "/reports/",
        json={"title": "Test"},
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert response.status_code == 403

def test_analytics_endpoint_returns_valid_data():
    """Test analytics endpoint with known data"""
    # Seed database with known violations
    seed_test_violations(count=10, days=7)
    
    response = client.get("/analytics/violation-trends?days=7")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["trends"]) == 7
    assert sum(day["count"] for day in data["trends"]) == 10
```

### 2. Property-Based Tests

**Purpose:** Verify universal properties hold across all inputs

**Framework:** Hypothesis (Python property-based testing library)

**Configuration:** Minimum 100 iterations per test

#### Property Test Examples

```python
# tests/test_properties.py

from hypothesis import given, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import pytest

# Property 1: User Authentication Round Trip
@given(
    microsoft_id=st.text(min_size=1, max_size=255),
    email=st.emails(),
    name=st.text(min_size=1, max_size=255)
)
def test_property_user_authentication_round_trip(microsoft_id, email, name):
    """
    Feature: aws-database-auth, Property 1: User Authentication Round Trip
    For any valid Microsoft user credentials, authenticating should create
    a user record with matching data.
    """
    # Create user
    user = db_service.get_or_create_user(
        microsoft_user_id=microsoft_id,
        email=email,
        name=name
    )
    
    # Verify user exists and data matches
    retrieved_user = db.query(User).filter_by(microsoft_user_id=microsoft_id).first()
    assert retrieved_user is not None
    assert retrieved_user.email == email
    assert retrieved_user.microsoft_user_id == microsoft_id

# Property 4: JWT Token Validation
@given(
    user_id=st.text(min_size=1),
    email=st.emails(),
    role=st.sampled_from(["Admin", "Safety_Officer", "Viewer"])
)
def test_property_jwt_token_validation(user_id, email, role):
    """
    Feature: aws-database-auth, Property 4: JWT Token Validation
    For any JWT token created by the system, verifying before expiration
    should return the original payload.
    """
    payload = {
        "microsoft_user_id": user_id,
        "email": email,
        "role": role
    }
    
    # Create token
    token = JWTHandler.create_access_token(payload)
    
    # Verify token
    decoded = JWTHandler.verify_token(token)
    
    # Check payload matches
    assert decoded["microsoft_user_id"] == user_id
    assert decoded["email"] == email
    assert decoded["role"] == role

# Property 5: Role-Based Access Control Enforcement
@given(
    user_role=st.sampled_from(["Viewer", "Safety_Officer", "Admin"]),
    required_role=st.sampled_from(["Viewer", "Safety_Officer", "Admin"])
)
def test_property_rbac_enforcement(user_role, required_role):
    """
    Feature: aws-database-auth, Property 5: RBAC Enforcement
    For any role combination, access should be granted only if user role
    is equal to or higher than required role.
    """
    role_hierarchy = {"Viewer": 1, "Safety_Officer": 2, "Admin": 3}
    
    user = User(role=user_role)
    should_allow = role_hierarchy[user_role] >= role_hierarchy[required_role]
    
    if should_allow:
        # Should not raise exception
        result = AuthMiddleware.require_role(required_role)(user)
        assert result == user
    else:
        # Should raise 403 Forbidden
        with pytest.raises(HTTPException) as exc:
            AuthMiddleware.require_role(required_role)(user)
        assert exc.value.status_code == 403

# Property 6: Database Query Pagination Consistency
@given(
    total_records=st.integers(min_value=10, max_value=100),
    page_size=st.integers(min_value=5, max_value=20)
)
def test_property_pagination_consistency(total_records, page_size):
    """
    Feature: aws-database-auth, Property 6: Pagination Consistency
    For any paginated query, combining pages should equal full result set.
    """
    # Create test reports
    reports = [create_test_report(index=i) for i in range(total_records)]
    
    # Get first page
    page1 = db_service.get_reports(limit=page_size, offset=0)
    
    # Get second page
    page2 = db_service.get_reports(limit=page_size, offset=page_size)
    
    # Get full result
    full = db_service.get_reports(limit=page_size * 2, offset=0)
    
    # Verify consistency
    combined = page1 + page2
    assert len(combined) == len(full)
    assert [r.id for r in combined] == [r.id for r in full]

# Property 8: Foreign Key Cascade Deletion
@given(
    violation_count=st.integers(min_value=1, max_value=10)
)
def test_property_cascade_deletion(violation_count):
    """
    Feature: aws-database-auth, Property 8: Foreign Key Cascade Deletion
    For any report with violations, deleting the report should delete all violations.
    """
    # Create report
    report = create_test_report()
    
    # Create violations
    violations = [
        create_test_violation(report_id=report.id)
        for _ in range(violation_count)
    ]
    violation_ids = [v.id for v in violations]
    
    # Delete report
    db.delete(report)
    db.commit()
    
    # Verify all violations are deleted
    remaining = db.query(Violation).filter(Violation.id.in_(violation_ids)).count()
    assert remaining == 0
```

### 3. Integration Tests

**Purpose:** Test end-to-end flows across multiple components

```python
# tests/test_integration.py

def test_full_authentication_flow():
    """Test complete OAuth flow from login to API access"""
    # 1. Get authorization URL
    response = client.get("/auth/login")
    assert response.status_code == 200
    auth_url = response.json()["authorization_url"]
    assert "login.microsoftonline.com" in auth_url
    
    # 2. Simulate Microsoft callback (mock)
    with mock_microsoft_oauth():
        response = client.get("/auth/callback?code=test_code&state=test_state")
        assert response.status_code == 200
        token = response.json()["access_token"]
    
    # 3. Use token to access protected endpoint
    response = client.get(
        "/reports/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_report_creation_and_retrieval_flow():
    """Test creating a report and retrieving it with violations"""
    token = create_test_token(role="Safety_Officer")
    
    # 1. Create report
    report_data = {
        "report_id": "TEST-001",
        "title": "Test Report",
        "text": "Test content",
        "location": "Site A",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/reports/",
        json=report_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    report_id = response.json()["report_id"]
    
    # 2. Add violation
    violation_data = {
        "violation_type": "No Hard Hat",
        "severity": "High",
        "timestamp": datetime.utcnow().isoformat(),
        "location": "Site A"
    }
    
    response = client.post(
        f"/reports/{report_id}/violations",
        json=violation_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    
    # 3. Retrieve report with violations
    response = client.get(
        f"/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["violations"]) == 1
    assert data["violations"][0]["violation_type"] == "No Hard Hat"
```

### Test Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Hypothesis settings
hypothesis_profile = default

[hypothesis]
max_examples = 100
deadline = 5000
```

**Test Coverage Target:** 85% overall, 95% for critical paths (auth, database)

---


## Database Migration Strategy

### Alembic Configuration

**File Structure:**
```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_indexes.py
│   └── 003_add_profile_picture.py
├── env.py
├── script.py.mako
└── alembic.ini
```

### Initial Migration

**File:** `alembic/versions/001_initial_schema.py`

```python
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('microsoft_user_id', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('role', sa.String(50), default='Viewer'),
        sa.Column('profile_picture_url', sa.Text()),
        sa.Column('organization', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime())
    )
    
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('format', sa.String(50)),
        sa.Column('metadata_json', JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create violations table
    op.create_table(
        'violations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('violation_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('osha_standard', sa.String(50)),
        sa.Column('confidence', sa.Float()),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Create detection_history table
    op.create_table(
        'detection_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('image_path', sa.String(500)),
        sa.Column('detection_count', sa.Integer(), default=0),
        sa.Column('violation_count', sa.Integer(), default=0),
        sa.Column('inference_time_ms', sa.Float()),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade():
    op.drop_table('detection_history')
    op.drop_table('violations')
    op.drop_table('reports')
    op.drop_table('users')
```

### Index Migration

**File:** `alembic/versions/002_add_indexes.py`

```python
"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2026-01-14

"""
from alembic import op

revision = '002'
down_revision = '001'

def upgrade():
    # Users indexes
    op.create_index('idx_users_microsoft_id', 'users', ['microsoft_user_id'])
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Reports indexes
    op.create_index('idx_reports_timestamp', 'reports', ['timestamp'])
    op.create_index('idx_reports_location', 'reports', ['location'])
    op.create_index('idx_reports_user_id', 'reports', ['user_id'])
    
    # Violations indexes
    op.create_index('idx_violations_type', 'violations', ['violation_type'])
    op.create_index('idx_violations_timestamp', 'violations', ['timestamp'])
    op.create_index('idx_violations_location', 'violations', ['location'])
    op.create_index('idx_violations_report_id', 'violations', ['report_id'])
    
    # Detection history indexes
    op.create_index('idx_detection_timestamp', 'detection_history', ['timestamp'])
    op.create_index('idx_detection_user_id', 'detection_history', ['user_id'])

def downgrade():
    # Drop all indexes
    op.drop_index('idx_detection_user_id')
    op.drop_index('idx_detection_timestamp')
    op.drop_index('idx_violations_report_id')
    op.drop_index('idx_violations_location')
    op.drop_index('idx_violations_timestamp')
    op.drop_index('idx_violations_type')
    op.drop_index('idx_reports_user_id')
    op.drop_index('idx_reports_location')
    op.drop_index('idx_reports_timestamp')
    op.drop_index('idx_users_email')
    op.drop_index('idx_users_microsoft_id')
```

### Migration Commands

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001

# Show current version
alembic current

# Show migration history
alembic history
```

---

## Infrastructure Setup

### AWS RDS Setup

**Step-by-Step Guide:**

1. **Create RDS Instance:**
```bash
# Using AWS CLI
aws rds create-db-instance \
    --db-instance-identifier siteguard-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --master-username siteguard_admin \
    --master-user-password <SECURE_PASSWORD> \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-xxxxx \
    --publicly-accessible \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "mon:04:00-mon:05:00" \
    --tags Key=Project,Value=SiteGuard Key=Environment,Value=Demo
```

2. **Configure Security Group:**
```bash
# Allow PostgreSQL access from your IP
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 5432 \
    --cidr <YOUR_IP>/32
```

3. **Get Connection Details:**
```bash
# Get endpoint
aws rds describe-db-instances \
    --db-instance-identifier siteguard-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text
```

4. **Test Connection:**
```bash
# Using psql
psql -h <RDS_ENDPOINT> -U siteguard_admin -d postgres

# Using Python
python scripts/test_db_connection.py
```

### Azure AD B2C Setup

**Step-by-Step Guide:**

1. **Create Azure AD B2C Tenant:**
   - Go to Azure Portal
   - Search "Azure AD B2C"
   - Click "Create a tenant"
   - Choose "Azure AD B2C"
   - Fill in details:
     - Organization name: SiteGuard
     - Initial domain name: siteguard
     - Country: Your country
   - Click "Create"

2. **Register Application:**
   - In Azure AD B2C tenant, go to "App registrations"
   - Click "New registration"
   - Fill in:
     - Name: SiteGuard AI
     - Supported account types: "Accounts in any identity provider or organizational directory"
     - Redirect URI: Web - `http://localhost:8501/callback`
   - Click "Register"
   - Note the "Application (client) ID"

3. **Create Client Secret:**
   - In app registration, go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "SiteGuard Demo"
   - Expires: 6 months
   - Click "Add"
   - Copy the secret value (only shown once!)

4. **Configure API Permissions:**
   - Go to "API permissions"
   - Click "Add a permission"
   - Choose "Microsoft Graph"
   - Select "Delegated permissions"
   - Add: User.Read, openid, profile, email
   - Click "Grant admin consent"

5. **Create User Flow (Optional):**
   - Go to "User flows"
   - Click "New user flow"
   - Choose "Sign up and sign in"
   - Select version: Recommended
   - Name: "signupsignin1"
   - Identity providers: Microsoft Account
   - User attributes: Email, Display Name
   - Click "Create"

### Environment Configuration

**File:** `.env`

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Database Configuration
DATABASE_URL=postgresql://siteguard_admin:PASSWORD@siteguard-db.xxxxx.us-east-1.rds.amazonaws.com:5432/siteguard

# Azure AD B2C Configuration
AZURE_AD_TENANT_ID=12345678-1234-1234-1234-123456789012
AZURE_AD_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_AD_CLIENT_SECRET=your_client_secret_here
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/12345678-1234-1234-1234-123456789012
AZURE_AD_REDIRECT_URI=http://localhost:8501/callback

# Application Configuration
SECRET_KEY=your-secret-key-for-jwt-signing-change-in-production
ENVIRONMENT=development
LOG_LEVEL=INFO

# API Configuration
API_BASE_URL=http://localhost:8000
STREAMLIT_SERVER_PORT=8501
```

**File:** `.env.example` (commit to git)

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/dbname

# Azure AD B2C Configuration
AZURE_AD_TENANT_ID=your_tenant_id_here
AZURE_AD_CLIENT_ID=your_client_id_here
AZURE_AD_CLIENT_SECRET=your_client_secret_here
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/your_tenant_id
AZURE_AD_REDIRECT_URI=http://localhost:8501/callback

# Application Configuration
SECRET_KEY=generate-a-secure-random-key
ENVIRONMENT=development
LOG_LEVEL=INFO

# API Configuration
API_BASE_URL=http://localhost:8000
STREAMLIT_SERVER_PORT=8501
```

---

## Deployment Guide

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Verify AWS credentials
aws sts get-caller-identity

# Verify Azure CLI (optional)
az account show
```

### Database Setup

```bash
# 1. Create RDS instance (see Infrastructure Setup above)

# 2. Set environment variables
export DATABASE_URL="postgresql://..."

# 3. Run migrations
alembic upgrade head

# 4. Verify tables created
python scripts/verify_database.py

# 5. Seed demo data
python scripts/seed_demo_data.py
```

### Application Startup

```bash
# Terminal 1: Start FastAPI backend
uvicorn app.api.main:app --reload --port 8000

# Terminal 2: Start Streamlit frontend
streamlit run app/web/streamlit_app_enhanced.py --server.port 8501
```

### Verification Checklist

- [ ] Database connection successful
- [ ] All tables created
- [ ] Indexes created
- [ ] Demo data seeded
- [ ] FastAPI health check passes: `curl http://localhost:8000/analytics/health`
- [ ] Streamlit loads without errors
- [ ] Microsoft login button appears
- [ ] OAuth redirect works
- [ ] User can authenticate
- [ ] Reports can be created
- [ ] Analytics display correctly

---

## Monitoring and Observability

### Health Checks

**Endpoint:** `GET /analytics/health`

**Response:**
```json
{
    "status": "healthy",
    "database": "connected",
    "timestamp": "2026-01-14T12:00:00Z"
}
```

### Logging Strategy

**Log Levels:**
- ERROR: Authentication failures, database errors, API errors
- WARNING: Slow queries, rate limiting, token expiration
- INFO: User login/logout, report creation, API requests
- DEBUG: SQL queries, OAuth flow steps

**Log Format:**
```json
{
    "timestamp": "2026-01-14T12:00:00Z",
    "level": "INFO",
    "service": "api",
    "message": "User authenticated successfully",
    "context": {
        "user_id": "12345",
        "email": "user@example.com",
        "ip_address": "192.168.1.1"
    }
}
```

### Metrics to Track

**Authentication Metrics:**
- Login attempts (success/failure)
- Token refresh rate
- Active sessions
- Average session duration

**Database Metrics:**
- Query execution time
- Connection pool usage
- Slow queries (>1s)
- Error rate

**API Metrics:**
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate by endpoint
- Rate limit hits

### Performance Monitoring

**Query Performance:**
```python
# Log slow queries
import time
import logging

def log_slow_query(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        if duration > 1.0:  # Log queries > 1 second
            logging.warning(f"Slow query: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper
```

---

## Security Considerations

### Authentication Security

1. **Token Security:**
   - JWT tokens expire after 1 hour
   - Tokens signed with strong secret key (256-bit)
   - Refresh tokens stored securely
   - No sensitive data in JWT payload

2. **OAuth Security:**
   - State parameter for CSRF protection
   - HTTPS required for production
   - Redirect URI whitelist
   - Client secret never exposed to client

3. **Session Security:**
   - Secure session cookies
   - HttpOnly flag set
   - SameSite=Strict
   - Session timeout after inactivity

### Database Security

1. **Connection Security:**
   - SSL/TLS encryption required
   - Connection string in environment variables
   - No hardcoded credentials
   - Least privilege database user

2. **Query Security:**
   - Parameterized queries (SQLAlchemy ORM)
   - No raw SQL with user input
   - Input validation on all endpoints
   - SQL injection prevention

3. **Data Security:**
   - Sensitive data encrypted at rest (RDS default)
   - Automated backups enabled
   - Point-in-time recovery available
   - Access logs enabled

### API Security

1. **Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/reports/")
@limiter.limit("100/minute")
async def get_reports():
    ...
```

2. **Input Validation:**
```python
from pydantic import BaseModel, validator

class ReportCreate(BaseModel):
    title: str
    location: str
    
    @validator('title')
    def title_length(cls, v):
        if len(v) > 500:
            raise ValueError('Title too long')
        return v
```

3. **CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Teardown Procedure

### Post-Demo Cleanup

**Script:** `scripts/teardown_aws.py`

```python
import boto3
import os

def teardown_aws_resources():
    """Delete all AWS resources"""
    rds = boto3.client('rds', region_name=os.getenv('AWS_REGION'))
    
    print("🗑️  Starting AWS resource teardown...")
    
    # 1. Delete RDS instance
    try:
        print("Deleting RDS instance...")
        rds.delete_db_instance(
            DBInstanceIdentifier='siteguard-db',
            SkipFinalSnapshot=True,
            DeleteAutomatedBackups=True
        )
        print("✅ RDS instance deletion initiated")
    except Exception as e:
        print(f"❌ Failed to delete RDS: {e}")
    
    # 2. Wait for deletion (optional)
    print("Waiting for RDS deletion (this may take 5-10 minutes)...")
    waiter = rds.get_waiter('db_instance_deleted')
    waiter.wait(DBInstanceIdentifier='siteguard-db')
    print("✅ RDS instance deleted")
    
    print("🎉 AWS teardown complete!")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all AWS resources? (yes/no): ")
    if confirm.lower() == "yes":
        teardown_aws_resources()
    else:
        print("Teardown cancelled")
```

**Manual Steps:**

1. **Delete Azure AD B2C Resources:**
   - Go to Azure Portal
   - Navigate to Azure AD B2C tenant
   - Delete app registration
   - (Optional) Delete tenant (it's free, so you can keep it)

2. **Verify Deletion:**
   - Check AWS Console - RDS should be gone
   - Check AWS Billing - no ongoing charges
   - Check Azure Portal - app registration deleted

3. **Clean Local Environment:**
```bash
# Remove .env file
rm .env

# Clear database connection
unset DATABASE_URL

# Remove cached credentials
rm -rf ~/.aws/credentials
```

### Cost Verification

```bash
# Check AWS costs
aws ce get-cost-and-usage \
    --time-period Start=2026-01-01,End=2026-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost

# Should show $0 if within free tier
```

---

## Demo Presentation Guide

### Demo Flow (5 minutes)

**1. Introduction (30 seconds)**
> "SiteGuard AI now uses enterprise-grade infrastructure with Microsoft authentication and AWS database."

**2. Authentication Demo (1 minute)**
- Show login page with "Sign in with Microsoft" button
- Click button → redirects to Microsoft
- Enter credentials → successful login
- Show user profile with picture and organization

**3. Report Generation (1.5 minutes)**
- Upload construction site image
- Generate safety report
- Show report saved to database
- Point out: "This is now persisted in AWS RDS PostgreSQL"

**4. Analytics Dashboard (1.5 minutes)**
- Show violation trends chart
- Display compliance rate
- Show location-based analytics
- Emphasize: "All data queried from database in real-time"

**5. Role-Based Access (30 seconds)**
- Show different features for different roles
- Demonstrate Admin-only settings page

**6. Architecture Slide (1 minute)**
- Show architecture diagram
- Highlight: Microsoft Azure AD B2C + AWS RDS
- Mention: "Production-ready, scalable, secure"

### Key Talking Points

✅ **Enterprise Authentication:** "Same SSO system used by Fortune 500 companies"
✅ **Cloud Database:** "AWS RDS with automatic backups and 99.95% uptime SLA"
✅ **Scalability:** "Can handle thousands of concurrent users"
✅ **Security:** "Role-based access control, encrypted connections, JWT tokens"
✅ **Cost-Effective:** "Running on free tier - $0 cost for demo"

---

**Document Version:** 1.0  
**Created:** January 14, 2026  
**Status:** Ready for Review

