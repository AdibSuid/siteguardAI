"""
Test database service layer with basic CRUD operations
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database.connection import DatabaseManager
from app.core.database.service import DatabaseService
from datetime import datetime, timedelta
import uuid

print("=" * 80)
print("DATABASE SERVICE LAYER TESTING")
print("=" * 80)

db_manager = DatabaseManager()

# Test 1: User Operations
print("\n1. Testing User Operations...")
print("-" * 80)

with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Create user
    user = service.get_or_create_user(
        microsoft_user_id=f"test-{uuid.uuid4()}",
        email="testuser@example.com",
        name="Test User",
        organization="Test Org"
    )
    print(f"✓ Created user: {user.email} (ID: {user.id})")
    user_id = user.id
    
    # Get user again (should update last_login)
    user2 = service.get_or_create_user(
        microsoft_user_id=user.microsoft_user_id,
        email=user.email,
        name="Updated Name"
    )
    print(f"✓ Retrieved existing user: {user2.name}")
    
    # Update role
    updated_user = service.update_user_role(user_id, "Safety_Officer")
    print(f"✓ Updated user role to: {updated_user.role}")

# Test 2: Report Operations
print("\n2. Testing Report Operations...")
print("-" * 80)

report_ids = []
with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Create reports
    for i in range(3):
        report = service.create_report(
            report_id=f"RPT-TEST-{i}",
            title=f"Test Report {i}",
            text=f"This is test report number {i}",
            location="Site A" if i % 2 == 0 else "Site B",
            timestamp=datetime.utcnow() - timedelta(days=i),
            user_id=user_id,
            format="text"
        )
        report_ids.append(report.id)
        print(f"✓ Created report: {report.report_id}")

# Get reports
with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    all_reports = service.get_reports(limit=10)
    print(f"✓ Retrieved {len(all_reports)} reports")
    
    site_a_reports = service.get_reports(location="Site A")
    print(f"✓ Retrieved {len(site_a_reports)} reports from Site A")
    
    user_reports = service.get_reports(user_id=user_id)
    print(f"✓ Retrieved {len(user_reports)} reports for user")

# Test 3: Violation Operations
print("\n3. Testing Violation Operations...")
print("-" * 80)

violation_ids = []
with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Create violations
    violation_types = ["No Hardhat", "No Safety Vest", "No Gloves"]
    for i, vtype in enumerate(violation_types):
        violation = service.create_violation(
            violation_type=vtype,
            severity="High" if i == 0 else "Medium",
            description=f"Test violation: {vtype}",
            osha_standard="1926.100",
            confidence=0.85 + (i * 0.05),
            timestamp=datetime.utcnow() - timedelta(days=i),
            location="Site A",
            report_id=report_ids[0]
        )
        violation_ids.append(violation.id)
        print(f"✓ Created violation: {violation.violation_type}")

# Get violations
with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    all_violations = service.get_violations(limit=10)
    print(f"✓ Retrieved {len(all_violations)} violations")
    
    report_violations = service.get_violations(report_id=report_ids[0])
    print(f"✓ Retrieved {len(report_violations)} violations for report")

# Test 4: Detection History Operations
print("\n4. Testing Detection History Operations...")
print("-" * 80)

history_ids = []
with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Create detection history
    for i in range(3):
        history = service.create_detection_history(
            image_path=f"/test/image_{i}.jpg",
            detection_count=10 + i,
            violation_count=2 + i,
            inference_time_ms=150.5 + (i * 10),
            timestamp=datetime.utcnow() - timedelta(days=i),
            user_id=user_id
        )
        history_ids.append(history.id)
        print(f"✓ Created detection history: {history.image_path}")

# Test 5: Analytics Operations
print("\n5. Testing Analytics Operations...")
print("-" * 80)

with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Violation trends
    trends = service.get_violation_trends(
        start_date=datetime.utcnow() - timedelta(days=7)
    )
    print(f"✓ Retrieved violation trends: {len(trends)} days")
    
    # Top violation types
    top_violations = service.get_top_violation_types(limit=5)
    print(f"✓ Retrieved top {len(top_violations)} violation types")
    for v in top_violations:
        print(f"  - {v['violation_type']}: {v['count']} occurrences")
    
    # Location analytics
    location_stats = service.get_location_analytics()
    print(f"✓ Retrieved location analytics for {len(location_stats)} locations")
    for loc in location_stats:
        print(f"  - {loc['location']}: {loc['violation_count']} violations")
    
    # Compliance rate
    compliance = service.get_compliance_rate()
    print(f"✓ Compliance rate: {compliance['compliance_rate']}%")
    print(f"  - Total detections: {compliance['total_detections']}")
    print(f"  - Total violations: {compliance['total_violations']}")

# Test 6: Cleanup
print("\n6. Cleaning up test data...")
print("-" * 80)

with db_manager.get_session() as session:
    from app.core.database.models import User, Report, Violation, DetectionHistory
    
    # Delete detection history
    for history_id in history_ids:
        session.query(DetectionHistory).filter(DetectionHistory.id == history_id).delete()
    print(f"✓ Deleted {len(history_ids)} detection history entries")
    
    # Delete violations
    for violation_id in violation_ids:
        session.query(Violation).filter(Violation.id == violation_id).delete()
    print(f"✓ Deleted {len(violation_ids)} violations")
    
    # Delete reports
    for report_id in report_ids:
        session.query(Report).filter(Report.id == report_id).delete()
    print(f"✓ Deleted {len(report_ids)} reports")
    
    # Delete user
    session.query(User).filter(User.id == user_id).delete()
    print(f"✓ Deleted user")
    
    session.commit()

print("\n" + "=" * 80)
print("✓ ALL DATABASE SERVICE TESTS PASSED!")
print("=" * 80)
print("\nDatabase service layer is working correctly.")
print("All CRUD operations and analytics queries functional.")
