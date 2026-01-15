"""
Property-based tests for analytics aggregation accuracy
Feature: aws-database-auth, Property 7: Analytics Aggregation Accuracy
Validates: Requirements 10.1, 10.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
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
from app.core.database.models import User, Violation, DetectionHistory
from datetime import datetime, timedelta
import uuid


@st.composite
def violations_over_time(draw):
    """Generate violations over a time period"""
    num_violations = draw(st.integers(min_value=5, max_value=20))
    base_date = datetime(2026, 1, 1)
    days_range = draw(st.integers(min_value=7, max_value=30))
    
    violations = []
    for _ in range(num_violations):
        day_offset = draw(st.integers(min_value=0, max_value=days_range))
        violation = {
            "violation_type": draw(st.sampled_from(["No Hardhat", "No Safety Vest", "No Gloves", "No Goggles"])),
            "severity": draw(st.sampled_from(["Low", "Medium", "High", "Critical"])),
            "description": f"Test violation {uuid.uuid4().hex[:8]}",
            "osha_standard": draw(st.sampled_from(["1926.100", "1926.102", "1926.95", "1926.28"])),
            "confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
            "timestamp": base_date + timedelta(days=day_offset),
            "location": draw(st.sampled_from(["Site A", "Site B", "Site C"]))
        }
        violations.append(violation)
    
    return violations, base_date, base_date + timedelta(days=days_range)


class TestAnalyticsAggregationAccuracy:
    """
    Property 7: Analytics Aggregation Accuracy
    
    Test that sum of daily trends equals total compliance count.
    """
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager for tests"""
        manager = DatabaseManager()
        manager.create_tables()
        yield manager
        manager.close()
    
    @given(violations_over_time())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_daily_trends_sum_equals_total_count(self, db_manager, violations_data):
        """
        Property: Sum of daily violation trends equals total violation count
        
        Feature: aws-database-auth, Property 7: Analytics Aggregation Accuracy
        Validates: Requirements 10.1, 10.2
        """
        violations, start_date, end_date = violations_data
        violation_ids = []
        
        try:
            # Create violations
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for violation_data in violations:
                    violation = service.create_violation(
                        violation_type=violation_data["violation_type"],
                        severity=violation_data["severity"],
                        description=violation_data["description"],
                        osha_standard=violation_data["osha_standard"],
                        confidence=violation_data["confidence"],
                        timestamp=violation_data["timestamp"],
                        location=violation_data["location"]
                    )
                    violation_ids.append(violation.id)
            
            # Get daily trends
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                trends = service.get_violation_trends(
                    start_date=start_date,
                    end_date=end_date
                )
            
            # Calculate sum of daily counts
            daily_sum = sum(trend['count'] for trend in trends)
            
            # Get total violations in period
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                all_violations = service.get_violations(
                    start_date=start_date,
                    end_date=end_date,
                    limit=1000
                )
                total_count = len(all_violations)
            
            # Verify sum equals total
            assert daily_sum == total_count, \
                f"Sum of daily trends ({daily_sum}) should equal total violations ({total_count})"
            
            # Verify sum equals original count
            assert daily_sum == len(violations), \
                f"Sum of daily trends ({daily_sum}) should equal created violations ({len(violations)})"
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for violation_id in violation_ids:
                    session.query(Violation).filter(Violation.id == violation_id).delete()
                session.commit()
    
    @given(violations_over_time())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_top_violations_sum_equals_total(self, db_manager, violations_data):
        """
        Property: Sum of top violation types equals total violation count
        
        Feature: aws-database-auth, Property 7: Analytics Aggregation Accuracy
        Validates: Requirements 10.1, 10.2
        """
        violations, start_date, end_date = violations_data
        violation_ids = []
        
        try:
            # Create violations
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for violation_data in violations:
                    violation = service.create_violation(
                        violation_type=violation_data["violation_type"],
                        severity=violation_data["severity"],
                        description=violation_data["description"],
                        osha_standard=violation_data["osha_standard"],
                        confidence=violation_data["confidence"],
                        timestamp=violation_data["timestamp"],
                        location=violation_data["location"]
                    )
                    violation_ids.append(violation.id)
            
            # Get top violation types (with high limit to get all)
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                top_violations = service.get_top_violation_types(
                    limit=100,
                    start_date=start_date,
                    end_date=end_date
                )
            
            # Calculate sum of violation type counts
            type_sum = sum(v['count'] for v in top_violations)
            
            # Verify sum equals total
            assert type_sum == len(violations), \
                f"Sum of violation types ({type_sum}) should equal total violations ({len(violations)})"
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for violation_id in violation_ids:
                    session.query(Violation).filter(Violation.id == violation_id).delete()
                session.commit()
    
    @given(violations_over_time())
    @settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_location_analytics_sum_equals_total(self, db_manager, violations_data):
        """
        Property: Sum of location analytics equals total violation count
        
        Feature: aws-database-auth, Property 7: Analytics Aggregation Accuracy
        Validates: Requirements 10.1, 10.2
        """
        violations, start_date, end_date = violations_data
        violation_ids = []
        
        try:
            # Create violations
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                for violation_data in violations:
                    violation = service.create_violation(
                        violation_type=violation_data["violation_type"],
                        severity=violation_data["severity"],
                        description=violation_data["description"],
                        osha_standard=violation_data["osha_standard"],
                        confidence=violation_data["confidence"],
                        timestamp=violation_data["timestamp"],
                        location=violation_data["location"]
                    )
                    violation_ids.append(violation.id)
            
            # Get location analytics
            with db_manager.get_session() as session:
                service = DatabaseService(session)
                location_stats = service.get_location_analytics(
                    start_date=start_date,
                    end_date=end_date
                )
            
            # Calculate sum of location counts
            location_sum = sum(loc['violation_count'] for loc in location_stats)
            
            # Verify sum equals total
            assert location_sum == len(violations), \
                f"Sum of location violations ({location_sum}) should equal total violations ({len(violations)})"
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for violation_id in violation_ids:
                    session.query(Violation).filter(Violation.id == violation_id).delete()
                session.commit()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
