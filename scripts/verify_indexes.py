"""
Verify that all indexes were created properly
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text, inspect

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)
inspector = inspect(engine)

print("Verifying database indexes...")
print("=" * 80)

tables = ['users', 'reports', 'violations', 'detection_history']

for table_name in tables:
    print(f"\n{table_name.upper()}:")
    print("-" * 80)
    
    indexes = inspector.get_indexes(table_name)
    if indexes:
        for idx in indexes:
            columns = ', '.join(idx['column_names'])
            unique = "UNIQUE" if idx['unique'] else "NON-UNIQUE"
            print(f"  - {idx['name']}: ({columns}) [{unique}]")
    else:
        print("  No indexes found")

print("\n" + "=" * 80)
print("Index verification complete!")
