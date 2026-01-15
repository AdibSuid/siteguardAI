"""
Property-based tests for report storage completeness
Feature: aws-database-auth, Property 3: Report Storage Completeness
Validates: Requirements 1.2, 1.3
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck
from sqlalchemy import text
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database.connection import DatabaseManager
from app.core.database.service import DatabaseService
from app.core.database.models import User, Report, Violation
from datetime import datetime
import uuid


# Hypothesis strategies for generating test data
@st.composite
def user_data(draw):
    """Generate random user data"""
    return {
        "microsoft_user_id": f"test-{draw(st.uuids())}",
        "email": draw(st.emails()),
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "role": draw(st.sampled_from(["Admin", "Safety_Officer", "Viewer"]))
    }


@st.composite
def report_with_violations(draw):
    """Generate random report with violations"""
    num_violations = draw(st.integers(min_value=1, max_value=5))
    
    # Use UUID to ensure unique report_id
    report_data = {
        "report_id": f"RPT-{uuid.uuid4().hex[:8].upper()}",
        "title": draw(st.text(min_size=10, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "text": draw(st.text(min_size=50, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "location": draw(st.sampled_from(["Site A", "Site B", "Site C", "Building 1", "Building 2"])),
        "timestamp": datetime.utcnow(),
        "format": draw(st.sampled_from(["text", "pdf", "html"]))
    }
    
    violations = []
    for _ in range(num_violations):
        violation = {
            "violation_type": draw(st.sampled_from(["No Hardhat", "No Safety Vest", "No Gloves", "No Goggles"])),
            "severity": draw(st.sampled_from(["Low", "Medium", "High", "Critical"])),
            "description": draw(st.text(min_size=20, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',)))),
            "osha_standard": draw(st.sampled_from(["1926.100", "1926.102", "1926.95", "1926.28"])),
            "confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
            "timestamp": datetime.utcnow(),
            "location": report_data["location"]
        }
        violations.append(violation)
    
    return report_data, violations


class TestReportStorageCompleteness:
    """
    Property 3: Report Storage Completeness
    
    Test that storing reports with violations preserves all violation data.
    """
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager for tests"""
        manager = DatabaseManager()
        manager.create_tables()
        yield manager
        manager.close()
    
    @given(user_data(), report_with_violations())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_report_with_violations_preserves_all_data(self, db_manager, user_data_dict, report_violations):
        """
        Property: For any report with violations, storing and retrieving preserves all violation data
        
        Feature: aws-database-auth, Property 3: Report Storage Completeness
        Validates: Requirements 1.2, 1.3
        """
        report_data, violations_data = report_violations
        
        user_id = None
        report_id = None
        
        try:
            # Create user
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                user = service.get_or_create_user(
                    microsoft_user_id=user_data_dict["microsoft_user_id"],
                    email=user_data_dict["email"],
                    name=user_data_dict["name"]
                )
                user_id = user.id
            
            # Create report
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                report = service.create_report(
                    report_id=report_data["report_id"],
                    title=report_data["title"],
                    text=report_data["text"],
                    location=report_data["location"],
                    timestamp=report_data["timestamp"],
                    user_id=user_id,
                    format=report_data["format"]
                )
                report_id = report.id
            
            # Create violations
            created_violation_ids = []
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for violation_data in violations_data:
                    violation = service.create_violation(
                        violation_type=violation_data["violation_type"],
                        severity=violation_data["severity"],
                        description=violation_data["description"],
                        osha_standard=violation_data["osha_standard"],
                        confidence=violation_data["confidence"],
                        timestamp=violation_data["timestamp"],
                        location=violation_data["location"],
                        report_id=report_id
                    )
                    created_violation_ids.append(violation.id)
            
            # Retrieve report and verify all data
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                retrieved_report = service.get_report_by_id(report_id)
                
                # Verify report data
                assert retrieved_report is not None, "Report should be retrievable"
                assert retrieved_report.report_id == report_data["report_id"]
                assert retrieved_report.title == report_data["title"]
                assert retrieved_report.text == report_data["text"]
                assert retrieved_report.location == report_data["location"]
                assert retrieved_report.format == report_data["format"]
                
                # Verify violations count
                assert len(retrieved_report.violations) == len(violations_data), \
                    f"Should have {len(violations_data)} violations, got {len(retrieved_report.violations)}"
                
                # Verify each violation's data (match by violation_type since order may vary)
                retrieved_violations_by_type = {v.violation_type: v for v in retrieved_report.violations}
                original_violations_by_type = {v["violation_type"]: v for v in violations_data}
                
                for violation_type, original in original_violations_by_type.items():
                    violation = retrieved_violations_by_type.get(violation_type)
                    assert violation is not None, f"Violation type {violation_type} not found"
                    assert violation.severity == original["severity"]
                    assert violation.description == original["description"]
                    assert violation.osha_standard == original["osha_standard"]
                    assert abs(violation.confidence - original["confidence"]) < 0.01
                    assert violation.location == original["location"]
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                if report_id:
                    session.query(Violation).filter(Violation.report_id == report_id).delete()
                    session.query(Report).filter(Report.id == report_id).delete()
                if user_id:
                    session.query(User).filter(User.id == user_id).delete()
                session.commit()
    
    @given(user_data(), st.lists(report_with_violations(), min_size=2, max_size=5))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_multiple_reports_maintain_independence(self, db_manager, user_data_dict, reports_list):
        """
        Property: Multiple reports with violations maintain data independence
        
        Feature: aws-database-auth, Property 3: Report Storage Completeness
        Validates: Requirements 1.2, 1.3
        """
        user_id = None
        report_ids = []
        
        try:
            # Create user
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                user = service.get_or_create_user(
                    microsoft_user_id=user_data_dict["microsoft_user_id"],
                    email=user_data_dict["email"],
                    name=user_data_dict["name"]
                )
                user_id = user.id
            
            # Create multiple reports with violations
            for report_data, violations_data in reports_list:
                with db_manager.get_session() as session:
                    service = DatabaseService(session)
                    report = service.create_report(
                        report_id=report_data["report_id"],
                        title=report_data["title"],
                        text=report_data["text"],
                        location=report_data["location"],
                        timestamp=report_data["timestamp"],
                        user_id=user_id,
                        format=report_data["format"]
                    )
                    report_ids.append(report.id)
                    
                    # Add violations to this report
                    for violation_data in violations_data:
                        service.create_violation(
                            violation_type=violation_data["violation_type"],
                            severity=violation_data["severity"],
                            description=violation_data["description"],
                            osha_standard=violation_data["osha_standard"],
                            confidence=violation_data["confidence"],
                            timestamp=violation_data["timestamp"],
                            location=violation_data["location"],
                            report_id=report.id
                        )
            
            # Verify each report has correct violations
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for i, report_id in enumerate(report_ids):
                    report = service.get_report_by_id(report_id)
                    expected_violations = len(reports_list[i][1])
                    
                    assert report is not None
                    assert len(report.violations) == expected_violations, \
                        f"Report {i} should have {expected_violations} violations, got {len(report.violations)}"
                    
                    # Verify violations belong to correct report
                    for violation in report.violations:
                        assert violation.report_id == report_id
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for report_id in report_ids:
                    session.query(Violation).filter(Violation.report_id == report_id).delete()
                    session.query(Report).filter(Report.id == report_id).delete()
                if user_id:
                    session.query(User).filter(User.id == user_id).delete()
                session.commit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
