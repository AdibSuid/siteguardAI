"""
Database service layer with CRUD operations and analytics
Provides high-level interface for database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.database.models import User, Report, Violation, DetectionHistory


class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self, session: Session):
        """
        Initialize database service with a session
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
    
    # ==================== User Operations ====================
    
    def get_or_create_user(
        self,
        microsoft_user_id: str,
        email: str,
        name: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        organization: Optional[str] = None
    ) -> User:
        """
        Get existing user or create new one
        
        Args:
            microsoft_user_id: Microsoft user ID from OAuth
            email: User email
            name: User display name
            profile_picture_url: URL to profile picture
            organization: User's organization
            
        Returns:
            User object
        """
        user = self.session.query(User).filter(
            User.microsoft_user_id == microsoft_user_id
        ).first()
        
        if user:
            # Update last login and profile info
            user.last_login = datetime.utcnow()
            if name:
                user.name = name
            if profile_picture_url:
                user.profile_picture_url = profile_picture_url
            if organization:
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
        
        return user
    
    def update_user_role(self, user_id: str, role: str) -> Optional[User]:
        """
        Update user role
        
        Args:
            user_id: User ID
            role: New role (Admin, Safety_Officer, Viewer)
            
        Returns:
            Updated user or None if not found
        """
        user = self.session.query(User).filter(User.id == user_id).first()
        if user:
            user.role = role
            self.session.commit()
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_microsoft_id(self, microsoft_user_id: str) -> Optional[User]:
        """Get user by Microsoft user ID"""
        return self.session.query(User).filter(
            User.microsoft_user_id == microsoft_user_id
        ).first()
    
    # ==================== Report Operations ====================
    
    def create_report(
        self,
        report_id: str,
        title: str,
        text: str,
        location: str,
        timestamp: datetime,
        user_id: str,
        format: str = "text",
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> Report:
        """
        Create a new report
        
        Args:
            report_id: Unique report identifier
            title: Report title
            text: Report content
            location: Location where report was generated
            timestamp: Report timestamp
            user_id: ID of user who created report
            format: Report format (text, pdf, html)
            metadata_json: Additional metadata
            
        Returns:
            Created report
        """
        report = Report(
            report_id=report_id,
            title=title,
            text=text,
            location=location,
            timestamp=timestamp,
            user_id=user_id,
            format=format,
            metadata_json=metadata_json
        )
        self.session.add(report)
        self.session.commit()
        return report
    
    def get_reports(
        self,
        user_id: Optional[str] = None,
        location: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Report]:
        """
        Get reports with optional filtering
        
        Args:
            user_id: Filter by user ID
            location: Filter by location
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of reports
        """
        query = self.session.query(Report)
        
        if user_id:
            query = query.filter(Report.user_id == user_id)
        if location:
            query = query.filter(Report.location == location)
        if start_date:
            query = query.filter(Report.timestamp >= start_date)
        if end_date:
            query = query.filter(Report.timestamp <= end_date)
        
        query = query.order_by(desc(Report.timestamp))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_report_by_id(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        return self.session.query(Report).filter(Report.id == report_id).first()
    
    def get_report_by_report_id(self, report_id: str) -> Optional[Report]:
        """Get report by report_id (unique identifier)"""
        return self.session.query(Report).filter(Report.report_id == report_id).first()
    
    # ==================== Violation Operations ====================
    
    def create_violation(
        self,
        violation_type: str,
        severity: str,
        description: str,
        osha_standard: str,
        confidence: float,
        timestamp: datetime,
        location: str,
        report_id: Optional[str] = None
    ) -> Violation:
        """
        Create a new violation
        
        Args:
            violation_type: Type of violation (e.g., "No Hardhat")
            severity: Severity level (Low, Medium, High, Critical)
            description: Violation description
            osha_standard: OSHA standard reference
            confidence: Detection confidence (0.0-1.0)
            timestamp: When violation was detected
            location: Where violation occurred
            report_id: Associated report ID
            
        Returns:
            Created violation
        """
        violation = Violation(
            violation_type=violation_type,
            severity=severity,
            description=description,
            osha_standard=osha_standard,
            confidence=confidence,
            timestamp=timestamp,
            location=location,
            report_id=report_id
        )
        self.session.add(violation)
        self.session.commit()
        return violation
    
    def get_violations(
        self,
        report_id: Optional[str] = None,
        location: Optional[str] = None,
        violation_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Violation]:
        """
        Get violations with optional filtering
        
        Args:
            report_id: Filter by report ID
            location: Filter by location
            violation_type: Filter by violation type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of violations
        """
        query = self.session.query(Violation)
        
        if report_id:
            query = query.filter(Violation.report_id == report_id)
        if location:
            query = query.filter(Violation.location == location)
        if violation_type:
            query = query.filter(Violation.violation_type == violation_type)
        if start_date:
            query = query.filter(Violation.timestamp >= start_date)
        if end_date:
            query = query.filter(Violation.timestamp <= end_date)
        
        query = query.order_by(desc(Violation.timestamp))
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    # ==================== Detection History Operations ====================
    
    def create_detection_history(
        self,
        image_path: str,
        detection_count: int,
        violation_count: int,
        inference_time_ms: float,
        timestamp: datetime,
        user_id: Optional[str] = None
    ) -> DetectionHistory:
        """
        Create detection history entry
        
        Args:
            image_path: Path to processed image
            detection_count: Number of detections
            violation_count: Number of violations
            inference_time_ms: Inference time in milliseconds
            timestamp: When detection occurred
            user_id: User who ran detection
            
        Returns:
            Created detection history entry
        """
        history = DetectionHistory(
            image_path=image_path,
            detection_count=detection_count,
            violation_count=violation_count,
            inference_time_ms=inference_time_ms,
            timestamp=timestamp,
            user_id=user_id
        )
        self.session.add(history)
        self.session.commit()
        return history
    
    # ==================== Analytics Operations ====================
    
    def get_violation_trends(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get violation trends grouped by date
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            location: Filter by location
            
        Returns:
            List of dicts with date and count
        """
        query = self.session.query(
            func.date(Violation.timestamp).label('date'),
            func.count(Violation.id).label('count')
        )
        
        if start_date:
            query = query.filter(Violation.timestamp >= start_date)
        if end_date:
            query = query.filter(Violation.timestamp <= end_date)
        if location:
            query = query.filter(Violation.location == location)
        
        query = query.group_by(func.date(Violation.timestamp))
        query = query.order_by(func.date(Violation.timestamp))
        
        results = query.all()
        return [{'date': str(r.date), 'count': r.count} for r in results]
    
    def get_top_violation_types(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most common violation types
        
        Args:
            limit: Maximum number of results
            start_date: Start date for analysis
            end_date: End date for analysis
            location: Filter by location
            
        Returns:
            List of dicts with violation_type and count
        """
        query = self.session.query(
            Violation.violation_type,
            func.count(Violation.id).label('count')
        )
        
        if start_date:
            query = query.filter(Violation.timestamp >= start_date)
        if end_date:
            query = query.filter(Violation.timestamp <= end_date)
        if location:
            query = query.filter(Violation.location == location)
        
        query = query.group_by(Violation.violation_type)
        query = query.order_by(desc('count'))
        query = query.limit(limit)
        
        results = query.all()
        return [{'violation_type': r.violation_type, 'count': r.count} for r in results]
    
    def get_location_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get violation statistics by location
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of dicts with location and violation count
        """
        query = self.session.query(
            Violation.location,
            func.count(Violation.id).label('violation_count')
        )
        
        if start_date:
            query = query.filter(Violation.timestamp >= start_date)
        if end_date:
            query = query.filter(Violation.timestamp <= end_date)
        
        query = query.group_by(Violation.location)
        query = query.order_by(desc('violation_count'))
        
        results = query.all()
        return [
            {'location': r.location, 'violation_count': r.violation_count}
            for r in results
        ]
    
    def get_compliance_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate compliance rate
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            location: Filter by location
            
        Returns:
            Dict with total_detections, violations, compliance_rate
        """
        # Get total detections
        detection_query = self.session.query(
            func.sum(DetectionHistory.detection_count).label('total_detections')
        )
        
        if start_date:
            detection_query = detection_query.filter(DetectionHistory.timestamp >= start_date)
        if end_date:
            detection_query = detection_query.filter(DetectionHistory.timestamp <= end_date)
        
        total_detections = detection_query.scalar() or 0
        
        # Get total violations
        violation_query = self.session.query(func.count(Violation.id))
        
        if start_date:
            violation_query = violation_query.filter(Violation.timestamp >= start_date)
        if end_date:
            violation_query = violation_query.filter(Violation.timestamp <= end_date)
        if location:
            violation_query = violation_query.filter(Violation.location == location)
        
        total_violations = violation_query.scalar() or 0
        
        # Calculate compliance rate
        if total_detections > 0:
            compliance_rate = ((total_detections - total_violations) / total_detections) * 100
        else:
            compliance_rate = 100.0
        
        return {
            'total_detections': total_detections,
            'total_violations': total_violations,
            'compliance_rate': round(compliance_rate, 2)
        }
