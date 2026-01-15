"""
Drop all tables to start fresh with Alembic migrations
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.core.database.connection import DatabaseManager

print("Dropping all tables...")
print("=" * 60)

db_manager = DatabaseManager()
db_manager.drop_tables()

print("All tables dropped successfully")
print("=" * 60)
