"""
Check what tables exist in the database
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")
engine = create_engine(database_url)

print("Checking existing tables in database...")
print("=" * 60)

with engine.connect() as conn:
    result = conn.execute(text("SHOW TABLES"))
    tables = [row[0] for row in result]
    
    if tables:
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
    else:
        print("No tables found in database")

print("=" * 60)
