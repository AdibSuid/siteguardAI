"""
Comprehensive test of Alembic migration setup
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect
from app.core.database.connection import DatabaseManager
from app.core.database.models import User, Report, Violation, DetectionHistory
from datetime import datetime
import uuid

print("=" * 80)
print("ALEMBIC MIGRATION SETUP VERIFICATION")
print("=" * 80)

# Test 1: Check Alembic version table
print("\n1. Checking Alembic version tracking...")
print("-" * 80)
database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    version = result.fetchone()
    if version:
        print(f"✓ Current migration version: {version[0]}")
    else:
        print("✗ No migration version found")
        sys.exit(1)

# Test 2: Verify all tables exist
print("\n2. Verifying all tables exist...")
print("-" * 80)
inspector = inspect(engine)
tables = inspector.get_table_names()
required_tables = ['users', 'reports', 'violations', 'detection_history', 'alembic_version']

for table in required_tables:
    if table in tables:
        print(f"✓ Table '{table}' exists")
    else:
        print(f"✗ Table '{table}' missing")
        sys.exit(1)

# Test 3: Verify indexes
print("\n3. Verifying performance indexes...")
print("-" * 80)
index_checks = {
    'users': ['ix_users_email', 'ix_users_microsoft_user_id'],
    'reports': ['ix_reports_timestamp', 'ix_reports_location', 'ix_reports_report_id'],
    'violations': ['ix_violations_violation_type', 'ix_violations_timestamp', 'ix_violations_location'],
    'detection_history': ['ix_detection_history_timestamp']
}

all_indexes_ok = True
for table, expected_indexes in index_checks.items():
    indexes = inspector.get_indexes(table)
    index_names = [idx['name'] for idx in indexes]
    for expected_idx in expected_indexes:
        if expected_idx in index_names:
            print(f"✓ Index '{expected_idx}' exists on '{table}'")
        else:
            print(f"✗ Index '{expected_idx}' missing on '{table}'")
            all_indexes_ok = False

if not all_indexes_ok:
    sys.exit(1)

# Test 4: Test database operations through connection manager
print("\n4. Testing database operations...")
print("-" * 80)
db_manager = DatabaseManager()

# Health check
if db_manager.health_check():
    print("✓ Database health check passed")
else:
    print("✗ Database health check failed")
    sys.exit(1)

# Create test user
test_user_id = None
try:
    with db_manager.get_session() as session:
        user = User(
            microsoft_user_id=f"test-alembic-{uuid.uuid4()}",
            email="alembic-test@example.com",
            name="Alembic Test User",
            role="Viewer"
        )
        session.add(user)
        session.commit()
        test_user_id = user.id
        print(f"✓ Created test user: {user.email}")
    
    # Create test report
    with db_manager.get_session() as session:
        report = Report(
            report_id=f"RPT-TEST-{uuid.uuid4().hex[:8]}",
            title="Alembic Test Report",
            text="This is a test report to verify migrations",
            location="Test Site",
            timestamp=datetime.utcnow(),
            user_id=test_user_id,
            format="text"
        )
        session.add(report)
        session.commit()
        report_id = report.id
        print(f"✓ Created test report: {report.report_id}")
    
    # Create test violation
    with db_manager.get_session() as session:
        violation = Violation(
            violation_type="No Hardhat",
            severity="High",
            description="Test violation for migration verification",
            osha_standard="1926.100",
            confidence=0.95,
            timestamp=datetime.utcnow(),
            location="Test Site",
            report_id=report_id
        )
        session.add(violation)
        session.commit()
        print(f"✓ Created test violation: {violation.violation_type}")
    
    # Verify foreign key relationships
    with db_manager.get_session() as session:
        report = session.query(Report).filter(Report.id == report_id).first()
        if report and report.violations:
            print(f"✓ Foreign key relationship working (report has {len(report.violations)} violation)")
        else:
            print("✗ Foreign key relationship not working")
            sys.exit(1)
    
    # Cleanup
    with db_manager.get_session() as session:
        session.query(Violation).filter(Violation.report_id == report_id).delete()
        session.query(Report).filter(Report.id == report_id).delete()
        session.query(User).filter(User.id == test_user_id).delete()
        session.commit()
        print("✓ Cleaned up test data")

except Exception as e:
    print(f"✗ Database operation failed: {e}")
    sys.exit(1)

# Test 5: Verify connection pool
print("\n5. Verifying connection pool configuration...")
print("-" * 80)
pool_info = db_manager.get_connection_info()
print(f"✓ Pool size: {pool_info['pool_size']}")
print(f"✓ Checked in: {pool_info['checked_in']}")
print(f"✓ Checked out: {pool_info['checked_out']}")
print(f"✓ Overflow: {pool_info['overflow']}")

print("\n" + "=" * 80)
print("✓ ALL ALEMBIC MIGRATION TESTS PASSED!")
print("=" * 80)
print("\nMigration setup is complete and working correctly.")
print("Database schema is properly versioned and tracked by Alembic.")
print("\nNext steps:")
print("  - Task 5: Implement database service layer")
print("  - Task 6: Checkpoint - Database integration complete")
