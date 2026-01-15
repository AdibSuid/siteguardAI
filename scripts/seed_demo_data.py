"""
Seed demo data for SiteGuard AI database
Creates realistic sample data for demonstration purposes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database.connection import DatabaseManager
from app.core.database.service import DatabaseService
from app.core.database.models import User, Report, Violation, DetectionHistory
from datetime import datetime, timedelta
import random
import uuid

print("=" * 80)
print("SEEDING DEMO DATA FOR SITEGUARD AI")
print("=" * 80)

db_manager = DatabaseManager()

# Demo data configuration
DEMO_USERS = [
    {
        "microsoft_user_id": "demo-admin-001",
        "email": "admin@siteguard-demo.com",
        "name": "Sarah Admin",
        "role": "Admin",
        "organization": "SiteGuard Demo Corp"
    },
    {
        "microsoft_user_id": "demo-officer-001",
        "email": "safety.officer@siteguard-demo.com",
        "name": "John Safety",
        "role": "Safety_Officer",
        "organization": "SiteGuard Demo Corp"
    },
    {
        "microsoft_user_id": "demo-viewer-001",
        "email": "viewer@siteguard-demo.com",
        "name": "Mike Viewer",
        "role": "Viewer",
        "organization": "SiteGuard Demo Corp"
    }
]

LOCATIONS = [
    "Construction Site A - Building 1",
    "Construction Site A - Building 2",
    "Construction Site B - Main Area",
    "Construction Site C - Warehouse",
    "Manufacturing Plant - Floor 1",
    "Manufacturing Plant - Floor 2"
]

VIOLATION_TYPES = [
    {"type": "No Hardhat", "severity": "Critical", "osha": "1926.100"},
    {"type": "No Safety Vest", "severity": "High", "osha": "1926.102"},
    {"type": "No Safety Goggles", "severity": "High", "osha": "1926.102"},
    {"type": "No Gloves", "severity": "Medium", "osha": "1926.95"},
    {"type": "No Steel-Toe Boots", "severity": "High", "osha": "1926.96"},
    {"type": "No Hearing Protection", "severity": "Medium", "osha": "1926.101"},
]

# Clear existing demo data
print("\n1. Clearing existing demo data...")
print("-" * 80)

with db_manager.get_session() as session:
    # Delete demo users and their related data (cascade will handle reports/violations)
    deleted_count = session.query(User).filter(
        User.microsoft_user_id.like('demo-%')
    ).delete(synchronize_session=False)
    session.commit()
    print(f"✓ Cleared {deleted_count} existing demo users and their data")

# Create demo users
print("\n2. Creating demo users...")
print("-" * 80)

user_ids = {}
for user_data in DEMO_USERS:
    with db_manager.get_session() as session:
        service = DatabaseService(session)
        user = service.get_or_create_user(
            microsoft_user_id=user_data["microsoft_user_id"],
            email=user_data["email"],
            name=user_data["name"],
            organization=user_data["organization"]
        )
        # Update role
        service.update_user_role(user.id, user_data["role"])
        user_ids[user_data["role"]] = user.id
        print(f"✓ Created user: {user.name} ({user.role})")

# Create demo reports with violations
print("\n3. Creating demo reports and violations...")
print("-" * 80)

# Generate reports over the last 30 days
num_reports = 25
reports_created = 0
violations_created = 0

for i in range(num_reports):
    days_ago = random.randint(0, 30)
    timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
    location = random.choice(LOCATIONS)
    
    # Randomly assign to Safety Officer or Admin
    user_id = random.choice([user_ids["Safety_Officer"], user_ids["Admin"]])
    
    with db_manager.get_session() as session:
        service = DatabaseService(session)
        
        # Create report
        report = service.create_report(
            report_id=f"RPT-DEMO-{i+1:04d}",
            title=f"Safety Inspection Report - {location}",
            text=f"Routine safety inspection conducted at {location}. "
                 f"Inspection completed on {timestamp.strftime('%Y-%m-%d %H:%M')}. "
                 f"Multiple PPE compliance issues identified and documented.",
            location=location,
            timestamp=timestamp,
            user_id=user_id,
            format="text",
            metadata_json={"inspection_type": "routine", "weather": "clear"}
        )
        reports_created += 1
        
        # Create 1-4 violations per report
        num_violations = random.randint(1, 4)
        for j in range(num_violations):
            violation_info = random.choice(VIOLATION_TYPES)
            
            violation = service.create_violation(
                violation_type=violation_info["type"],
                severity=violation_info["severity"],
                description=f"Worker observed without required {violation_info['type'].lower()} "
                           f"in {location}. Immediate corrective action required.",
                osha_standard=violation_info["osha"],
                confidence=random.uniform(0.75, 0.99),
                timestamp=timestamp + timedelta(minutes=random.randint(1, 30)),
                location=location,
                report_id=report.id
            )
            violations_created += 1

print(f"✓ Created {reports_created} demo reports")
print(f"✓ Created {violations_created} demo violations")

# Create detection history
print("\n4. Creating detection history...")
print("-" * 80)

history_created = 0
for i in range(50):
    days_ago = random.randint(0, 30)
    timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
    
    # Randomly assign to any user
    user_id = random.choice(list(user_ids.values()))
    
    with db_manager.get_session() as session:
        service = DatabaseService(session)
        
        detection_count = random.randint(5, 25)
        violation_count = random.randint(0, min(5, detection_count))
        
        history = service.create_detection_history(
            image_path=f"/demo/images/detection_{i+1:04d}.jpg",
            detection_count=detection_count,
            violation_count=violation_count,
            inference_time_ms=random.uniform(100, 300),
            timestamp=timestamp,
            user_id=user_id
        )
        history_created += 1

print(f"✓ Created {history_created} detection history entries")

# Display analytics summary
print("\n5. Demo Data Analytics Summary...")
print("-" * 80)

with db_manager.get_session() as session:
    service = DatabaseService(session)
    
    # Violation trends
    trends = service.get_violation_trends(
        start_date=datetime.utcnow() - timedelta(days=30)
    )
    print(f"✓ Violation trends: {len(trends)} days with data")
    
    # Top violation types
    top_violations = service.get_top_violation_types(limit=5)
    print(f"\n✓ Top 5 Violation Types:")
    for v in top_violations:
        print(f"  - {v['violation_type']}: {v['count']} occurrences")
    
    # Location analytics
    location_stats = service.get_location_analytics()
    print(f"\n✓ Violations by Location:")
    for loc in location_stats[:5]:  # Top 5 locations
        print(f"  - {loc['location']}: {loc['violation_count']} violations")
    
    # Compliance rate
    compliance = service.get_compliance_rate(
        start_date=datetime.utcnow() - timedelta(days=30)
    )
    print(f"\n✓ Overall Compliance Rate: {compliance['compliance_rate']}%")
    print(f"  - Total Detections: {compliance['total_detections']}")
    print(f"  - Total Violations: {compliance['total_violations']}")

# Summary
print("\n" + "=" * 80)
print("DEMO DATA SEEDING COMPLETE")
print("=" * 80)

print(f"\n✅ Successfully seeded demo data:")
print(f"  - {len(DEMO_USERS)} demo users (Admin, Safety Officer, Viewer)")
print(f"  - {reports_created} safety inspection reports")
print(f"  - {violations_created} PPE violations")
print(f"  - {history_created} detection history entries")
print(f"  - Data spans last 30 days")

print(f"\n📊 Demo Users:")
for user_data in DEMO_USERS:
    print(f"  - {user_data['name']} ({user_data['role']}): {user_data['email']}")

print(f"\n🎯 Use this data to demonstrate:")
print(f"  - Report generation and viewing")
print(f"  - Violation tracking and analytics")
print(f"  - Compliance rate calculations")
print(f"  - Time-series trend analysis")
print(f"  - Location-based statistics")
print(f"  - Role-based access control")

print("\n" + "=" * 80)
