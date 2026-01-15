"""
Property-based tests for database connection persistence
Feature: aws-database-auth, Property 2: Database Connection Persistence
Validates: Requirements 1.1, 1.5
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
from app.core.database.models import User, Report, Violation, DetectionHistory
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
def report_data(draw, user_id):
    """Generate random report data"""
    return {
        "report_id": f"RPT-{draw(st.integers(min_value=1000, max_value=9999))}",
        "title": draw(st.text(min_size=10, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "text": draw(st.text(min_size=50, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "location": draw(st.sampled_from(["Site A", "Site B", "Site C", "Building 1", "Building 2"])),
        "timestamp": datetime.utcnow(),
        "user_id": user_id,
        "format": draw(st.sampled_from(["text", "pdf", "html"]))
    }


@st.composite
def violation_data(draw, report_id):
    """Generate random violation data"""
    return {
        "violation_type": draw(st.sampled_from(["No Hardhat", "No Safety Vest", "No Gloves", "No Goggles"])),
        "severity": draw(st.sampled_from(["Low", "Medium", "High", "Critical"])),
        "description": draw(st.text(min_size=20, max_size=200, alphabet=st.characters(blacklist_categories=('Cs',)))),
        "osha_standard": draw(st.sampled_from(["1926.100", "1926.102", "1926.95", "1926.28"])),
        "confidence": draw(st.floats(min_value=0.5, max_value=1.0)),
        "timestamp": datetime.utcnow(),
        "location": draw(st.sampled_from(["Site A", "Site B", "Site C"])),
        "report_id": report_id
    }


class TestDatabaseConnectionPersistence:
    """
    Property 2: Database Connection Persistence
    
    Test that database operations don't corrupt the connection pool.
    The connection should remain healthy after various database operations.
    """
    
    @pytest.fixture(scope="class")
    def db_manager(self):
        """Create database manager for tests"""
        manager = DatabaseManager()
        # Ensure tables exist
        manager.create_tables()
        yield manager
        # Cleanup after tests
        manager.close()
    
    @given(user_data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_connection_persists_after_user_operations(self, db_manager, user_data_dict):
        """
        Property: For any user data, creating and deleting a user should not corrupt the connection pool
        
        Feature: aws-database-auth, Property 2: Database Connection Persistence
        Validates: Requirements 1.1, 1.5
        """
        # Verify connection is healthy before operation
        assert db_manager.health_check(), "Connection should be healthy before operation"
        
        user_id = None
        try:
            # Create user
            with db_manager.get_session() as session:
                user = User(**user_data_dict)
                session.add(user)
                session.commit()
                user_id = user.id
            
            # Verify connection is still healthy
            assert db_manager.health_check(), "Connection should be healthy after user creation"
            
            # Delete user
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    session.delete(user)
                    session.commit()
            
            # Verify connection is still healthy after deletion
            assert db_manager.health_check(), "Connection should be healthy after user deletion"
            
        except Exception as e:
            # Even if operation fails, connection should remain healthy
            assert db_manager.health_check(), f"Connection should remain healthy even after error: {e}"
            raise
    
    @given(st.integers(min_value=5, max_value=20))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_connection_persists_after_multiple_operations(self, db_manager, num_operations):
        """
        Property: For any number of sequential operations, the connection pool should remain healthy
        
        Feature: aws-database-auth, Property 2: Database Connection Persistence
        Validates: Requirements 1.1, 1.5
        """
        # Verify initial health
        assert db_manager.health_check(), "Connection should be healthy initially"
        
        user_ids = []
        
        try:
            # Perform multiple create operations
            for i in range(num_operations):
                with db_manager.get_session() as session:
                    user = User(
                        microsoft_user_id=f"test-multi-{uuid.uuid4()}",
                        email=f"test{i}@example.com",
                        name=f"Test User {i}",
                        role="Viewer"
                    )
                    session.add(user)
                    session.commit()
                    user_ids.append(user.id)
                
                # Check health after each operation
                assert db_manager.health_check(), f"Connection should be healthy after operation {i+1}"
            
            # Verify connection pool info
            info = db_manager.get_connection_info()
            assert info['pool_size'] > 0, "Pool should have connections"
            assert info['total_connections'] <= info['pool_size'] + db_manager.engine.pool.overflow(), \
                "Total connections should not exceed pool size + overflow"
            
        finally:
            # Cleanup
            with db_manager.get_session() as session:
                for user_id in user_ids:
                    user = session.query(User).filter(User.id == user_id).first()
                    if user:
                        session.delete(user)
                session.commit()
            
            # Verify health after cleanup
            assert db_manager.health_check(), "Connection should be healthy after cleanup"
    
    @given(user_data())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_connection_persists_after_rollback(self, db_manager, user_data_dict):
        """
        Property: For any operation that fails and rolls back, the connection should remain healthy
        
        Feature: aws-database-auth, Property 2: Database Connection Persistence
        Validates: Requirements 1.1, 1.5
        """
        # Verify initial health
        assert db_manager.health_check(), "Connection should be healthy initially"
        
        try:
            # Attempt operation that will fail (duplicate microsoft_user_id)
            with db_manager.get_session() as session:
                user1 = User(**user_data_dict)
                session.add(user1)
                session.commit()
                user1_id = user1.id
            
            # Try to create duplicate (should fail)
            try:
                with db_manager.get_session() as session:
                    user2 = User(**user_data_dict)  # Same data, will violate unique constraint
                    session.add(user2)
                    session.commit()
            except Exception:
                # Expected to fail
                pass
            
            # Verify connection is still healthy after rollback
            assert db_manager.health_check(), "Connection should be healthy after rollback"
            
            # Cleanup
            with db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user1_id).first()
                if user:
                    session.delete(user)
                    session.commit()
            
        except Exception as e:
            # Connection should remain healthy even if test fails
            assert db_manager.health_check(), f"Connection should remain healthy: {e}"
            raise
    
    def test_connection_pool_does_not_leak(self, db_manager):
        """
        Property: Connection pool should not leak connections
        
        Feature: aws-database-auth, Property 2: Database Connection Persistence
        Validates: Requirements 1.1, 1.5
        """
        # Get initial pool state
        initial_info = db_manager.get_connection_info()
        initial_checked_out = initial_info['checked_out']
        
        # Perform multiple operations
        for i in range(20):
            with db_manager.get_session() as session:
                session.execute(text("SELECT 1"))
        
        # Get final pool state
        final_info = db_manager.get_connection_info()
        final_checked_out = final_info['checked_out']
        
        # Verify no connections are leaked
        assert final_checked_out == initial_checked_out, \
            f"Connection leak detected: initial={initial_checked_out}, final={final_checked_out}"
        
        # Verify health
        assert db_manager.health_check(), "Connection should be healthy after operations"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
