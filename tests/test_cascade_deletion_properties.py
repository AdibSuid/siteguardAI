"""
Property-based tests for foreign key cascade deletion
Feature: aws-database-auth, Property 8: Foreign Key Cascade Deletion
Validates: Requirements 4.5
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
from app.core.database.models import User, Report, Violation, DetectionHistory
from datetime import datetime
import uuid


@st.composite
def user_with_reports(draw):
    """Generate user with multiple reports"""
    user_data = {
        "microsoft_user_id": f"test-{draw(st.uuids())}",
        "email": draw(st.emails()),
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))),
    }
    
    num_reports = draw(st.integers(min_value=2, max_value=5))
    reports = []
    
    for _ in range(num_reports):
        report = {
            "report_id": f"RPT-{draw(st.integers(min_value=1000, max_value=9999))}",
            "title": draw(st.text(min_size=10, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',)))),
            "text": draw(st.text(min_size=50, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',)))),
            "location": draw(st.sampled_from(["Site A", "Site B", "Site C"])),
            "timestamp": datetime.utcnow(),
            "format": "text",
            "num_violations": draw(st.integers(min_value=1, max_value=3))
        }
        reports.append(report)
    
    return user_data, reports


class TestForeignKeyCascadeDeletion:
    """
    Property 8: Foreign Key Cascade Deletion
    
    Test that deleting reports cascades to violations.
    """
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager for tests"""
        manager = DatabaseManager()
        manager.create_tables()
        yield manager
        manager.close()
    
    @given(user_with_reports())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_deleting_report_cascades_to_violations(self, db_manager, user_reports_data):
        """
        Property: Deleting a report cascades to delete all its violations
        
        Feature: aws-database-auth, Property 8: Foreign Key Cascade Deletion
        Validates: Requirements 4.5
        """
        user_data, reports_data = user_reports_data
        user_id = None
        report_ids = []
        violation_ids = []
        
        try:
            # Create user
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                user = service.get_or_create_user(
                    microsoft_user_id=user_data["microsoft_user_id"],
                    email=user_data["email"],
                    name=user_data["name"]
                )
                user_id = user.id
            
            # Create reports with violations
            for report_data in reports_data:
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
                    
                    # Create violations for this report
                    for i in range(report_data["num_violations"]):
                        violation = service.create_violation(
                            violation_type=f"Violation Type {i}",
                            severity="Medium",
                            description=f"Test violation {i} for report {report.report_id}",
                            osha_standard="1926.100",
                            confidence=0.85,
                            timestamp=datetime.utcnow(),
                            location=report_data["location"],
                            report_id=report.id
                        )
                        violation_ids.append(violation.id)
            
            # Verify all violations exist
            with db_manager.get_session() as session:
                for violation_id in violation_ids:
                    violation = session.query(Violation).filter(Violation.id == violation_id).first()
                    assert violation is not None, f"Violation {violation_id} should exist"
            
            # Delete first report
            deleted_report_id = report_ids[0]
            with db_manager.get_session() as session:
                report = session.query(Report).filter(Report.id == deleted_report_id).first()
                # Count violations before deletion
                violations_before = len(report.violations)
                assert violations_before > 0, "Report should have violations"
                
                # Get violation IDs for this report
                deleted_violation_ids = [v.id for v in report.violations]
                
                # Delete report
                session.delete(report)
                session.commit()
            
            # Verify report is deleted
            with db_manager.get_session() as session:
                report = session.query(Report).filter(Report.id == deleted_report_id).first()
                assert report is None, "Report should be deleted"
            
            # Verify violations are cascaded deleted
            with db_manager.get_session() as session:
                for violation_id in deleted_violation_ids:
                    violation = session.query(Violation).filter(Violation.id == violation_id).first()
                    assert violation is None, \
                        f"Violation {violation_id} should be cascade deleted with report"
            
            # Verify other reports and violations still exist
            with db_manager.get_session() as session:
                for report_id in report_ids[1:]:
                    report = session.query(Report).filter(Report.id == report_id).first()
                    assert report is not None, f"Other report {report_id} should still exist"
                    assert len(report.violations) > 0, "Other reports should still have violations"
            
        finally:
            # Cleanup remaining data
            with db_manager.get_session() as session:
                for report_id in report_ids[1:]:  # Skip first one, already deleted
                    session.query(Violation).filter(Violation.report_id == report_id).delete()
                    session.query(Report).filter(Report.id == report_id).delete()
                if user_id:
                    session.query(User).filter(User.id == user_id).delete()
                session.commit()
    
    @given(user_with_reports())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_deleting_user_cascades_to_reports_and_violations(self, db_manager, user_reports_data):
        """
        Property: Deleting a user cascades to delete all reports and violations
        
        Feature: aws-database-auth, Property 8: Foreign Key Cascade Deletion
        Validates: Requirements 4.5
        """
        user_data, reports_data = user_reports_data
        user_id = None
        report_ids = []
        violation_ids = []
        
        try:
            # Create user
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                user = service.get_or_create_user(
                    microsoft_user_id=user_data["microsoft_user_id"],
                    email=user_data["email"],
                    name=user_data["name"]
                )
                user_id = user.id
            
            # Create reports with violations
            for report_data in reports_data:
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
                    
                    # Create violations for this report
                    for i in range(report_data["num_violations"]):
                        violation = service.create_violation(
                            violation_type=f"Violation Type {i}",
                            severity="Medium",
                            description=f"Test violation {i}",
                            osha_standard="1926.100",
                            confidence=0.85,
                            timestamp=datetime.utcnow(),
                            location=report_data["location"],
                            report_id=report.id
                        )
                        violation_ids.append(violation.id)
            
            # Count total reports and violations
            total_reports = len(report_ids)
            total_violations = len(violation_ids)
            
            assert total_reports > 0, "Should have created reports"
            assert total_violations > 0, "Should have created violations"
            
            # Delete user
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                session.delete(user)
                session.commit()
            
            # Verify user is deleted
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                assert user is None, "User should be deleted"
            
            # Verify all reports are cascade deleted
            with db_manager.get_session() as session:
                for report_id in report_ids:
                    report = session.query(Report).filter(Report.id == report_id).first()
                    assert report is None, \
                        f"Report {report_id} should be cascade deleted with user"
            
            # Verify all violations are cascade deleted
            with db_manager.get_session() as session:
                for violation_id in violation_ids:
                    violation = session.query(Violation).filter(Violation.id == violation_id).first()
                    assert violation is None, \
                        f"Violation {violation_id} should be cascade deleted with report"
            
            # Clear user_id so cleanup doesn't try to delete again
            user_id = None
            report_ids = []
            
        finally:
            # Cleanup (should be empty due to cascade)
            with db_manager.get_session() as session:
                for report_id in report_ids:
                    session.query(Violation).filter(Violation.report_id == report_id).delete()
                    session.query(Report).filter(Report.id == report_id).delete()
                if user_id:
                    session.query(User).filter(User.id == user_id).delete()
                session.commit()
    
    @given(user_with_reports())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_deleting_user_cascades_to_detection_history(self, db_manager, user_reports_data):
        """
        Property: Deleting a user cascades to delete detection history
        
        Feature: aws-database-auth, Property 8: Foreign Key Cascade Deletion
        Validates: Requirements 4.5
        """
        user_data, _ = user_reports_data
        user_id = None
        history_ids = []
        
        try:
            # Create user
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                user = service.get_or_create_user(
                    microsoft_user_id=user_data["microsoft_user_id"],
                    email=user_data["email"],
                    name=user_data["name"]
                )
                user_id = user.id
            
            # Create detection history entries
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for i in range(3):
                    history = service.create_detection_history(
                        image_path=f"/test/image_{i}.jpg",
                        detection_count=10,
                        violation_count=2,
                        inference_time_ms=150.5,
                        timestamp=datetime.utcnow(),
                        user_id=user_id
                    )
                    history_ids.append(history.id)
            
            # Verify history entries exist
            with db_manager.get_session() as session:
                for history_id in history_ids:
                    history = session.query(DetectionHistory).filter(
                        DetectionHistory.id == history_id
                    ).first()
                    assert history is not None, "Detection history should exist"
            
            # Delete user
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                session.delete(user)
                session.commit()
            
            # Verify detection history is cascade deleted
            with db_manager.get_session() as session:
                for history_id in history_ids:
                    history = session.query(DetectionHistory).filter(
                        DetectionHistory.id == history_id
                    ).first()
                    assert history is None, \
                        f"Detection history {history_id} should be cascade deleted with user"
            
            # Clear user_id so cleanup doesn't try to delete again
            user_id = None
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for history_id in history_ids:
                    session.query(DetectionHistory).filter(DetectionHistory.id == history_id).delete()
                if user_id:
                    session.query(User).filter(User.id == user_id).delete()
                session.commit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
