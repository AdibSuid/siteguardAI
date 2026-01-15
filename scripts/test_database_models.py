#!/usr/bin/env python3
"""
Test database models and connection
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database.connection import DatabaseManager
from app.core.database.models import Base, User, Report, Violation, DetectionHistory

def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        print("✓ DatabaseManager initialized")
        
        # Test health check
        if db_manager.health_check():
            print("✓ Database health check passed")
        else:
            print("✗ Database health check failed")
            return False
        
        # Get connection info
        info = db_manager.get_connection_info()
        print(f"✓ Connection pool info:")
        print(f"    Pool size: {info['pool_size']}")
        print(f"    Checked in: {info['checked_in']}")
        print(f"    Checked out: {info['checked_out']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_create_tables():
    """Test table creation"""
    print("\n" + "=" * 60)
    print("Testing Table Creation")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        
        # Create tables
        print("Creating tables...")
        db_manager.create_tables()
        print("✓ Tables created successfully")
        
        # Verify tables exist
        with db_manager.get_session() as session:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_name IN ('users', 'reports', 'violations', 'detection_history')
            """))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = ['users', 'reports', 'violations', 'detection_history']
            for table in expected_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 60)
    print("Testing Basic CRUD Operations")
    print("=" * 60)
    
    try:
        db_manager = DatabaseManager()
        
        # Create a test user
        with db_manager.get_session() as session:
            user = User(
                microsoft_user_id="test-user-123",
                email="test@example.com",
                name="Test User",
                role="Viewer"
            )
            session.add(user)
            session.commit()
            user_id = user.id
            print(f"✓ Created test user: {user.email} (ID: {user_id})")
        
        # Read the user
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                print(f"✓ Retrieved user: {user.email}")
            else:
                print("✗ Failed to retrieve user")
                return False
        
        # Update the user
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            user.role = "Safety_Officer"
            session.commit()
            print(f"✓ Updated user role to: {user.role}")
        
        # Delete the user
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            session.delete(user)
            session.commit()
            print("✓ Deleted test user")
        
        # Verify deletion
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user is None:
                print("✓ Verified user deletion")
            else:
                print("✗ User still exists after deletion")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing Database Models and Connection")
    print()
    
    # Test connection
    if not test_connection():
        print("\n✗ Connection test failed")
        sys.exit(1)
    
    # Test table creation
    if not test_create_tables():
        print("\n✗ Table creation test failed")
        sys.exit(1)
    
    # Test basic operations
    if not test_basic_operations():
        print("\n✗ CRUD operations test failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nDatabase models and connection are working correctly.")
    print("Next steps:")
    print("  1. Set up Alembic migrations (Task 4)")
    print("  2. Implement database service layer (Task 5)")

if __name__ == "__main__":
    main()
