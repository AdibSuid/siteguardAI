#!/usr/bin/env python3
"""
Validate AWS RDS PostgreSQL connection
Tests database connectivity and basic operations
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_psycopg2_import():
    """Test if psycopg2 is installed"""
    try:
        import psycopg2
        print("✓ psycopg2 is installed")
        return True
    except ImportError:
        print("✗ psycopg2 is not installed")
        print("  Install with: pip install psycopg2-binary")
        return False

def test_sqlalchemy_import():
    """Test if SQLAlchemy is installed"""
    try:
        import sqlalchemy
        print(f"✓ SQLAlchemy is installed (version {sqlalchemy.__version__})")
        return True
    except ImportError:
        print("✗ SQLAlchemy is not installed")
        print("  Install with: pip install sqlalchemy")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    required_vars = [
        "DATABASE_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"✗ {var} is not set")
        else:
            # Mask password in output
            if "PASSWORD" in var:
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"✓ {var} = {display_value}")
    
    if missing:
        print(f"\n✗ Missing environment variables: {', '.join(missing)}")
        print("  Add these to your .env file")
        return False
    
    return True

def test_database_connection():
    """Test connection to RDS PostgreSQL"""
    try:
        import psycopg2
        
        # Get connection parameters
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        print(f"\nAttempting to connect to: {db_host}:{db_port}/{db_name}")
        
        # Attempt connection
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        
        print("✓ Successfully connected to database")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL version: {version.split(',')[0]}")
        
        # Test database name
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()[0]
        print(f"✓ Connected to database: {current_db}")
        
        # Test user
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        print(f"✓ Connected as user: {current_user}")
        
        # Close connection
        cursor.close()
        conn.close()
        print("✓ Connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("  1. Verify RDS instance is 'Available' in AWS Console")
        print("  2. Check security group allows your IP on port 5432")
        print("  3. Verify endpoint URL is correct")
        print("  4. Ensure 'Public access' is enabled")
        print("  5. Check your IP hasn't changed (if using dynamic IP)")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    try:
        from sqlalchemy import create_engine, text
        
        database_url = os.getenv("DATABASE_URL")
        
        print(f"\nTesting SQLAlchemy connection...")
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ SQLAlchemy connection successful")
            
            # Test table listing
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"✓ Found {len(tables)} existing tables:")
                for table in tables:
                    print(f"    - {table[0]}")
            else:
                print("✓ No tables yet (expected for new database)")
        
        return True
        
    except Exception as e:
        print(f"✗ SQLAlchemy connection failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("AWS RDS PostgreSQL Connection Validation")
    print("=" * 60)
    
    print("\n1. Checking Python packages...")
    print("-" * 60)
    psycopg2_ok = test_psycopg2_import()
    sqlalchemy_ok = test_sqlalchemy_import()
    
    if not (psycopg2_ok and sqlalchemy_ok):
        print("\n✗ Missing required packages. Install them first:")
        print("  pip install psycopg2-binary sqlalchemy python-dotenv")
        sys.exit(1)
    
    print("\n2. Checking environment variables...")
    print("-" * 60)
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n✗ Environment variables not configured properly")
        print("  See scripts/setup_rds.md for instructions")
        sys.exit(1)
    
    print("\n3. Testing database connection...")
    print("-" * 60)
    conn_ok = test_database_connection()
    
    if not conn_ok:
        print("\n✗ Database connection failed")
        print("  See scripts/setup_rds.md for troubleshooting")
        sys.exit(1)
    
    print("\n4. Testing SQLAlchemy connection...")
    print("-" * 60)
    sqlalchemy_conn_ok = test_sqlalchemy_connection()
    
    if not sqlalchemy_conn_ok:
        print("\n✗ SQLAlchemy connection failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All validation tests passed!")
    print("=" * 60)
    print("\nYour RDS PostgreSQL database is ready to use.")
    print("Next steps:")
    print("  1. Run database migrations: alembic upgrade head")
    print("  2. Seed demo data: python scripts/seed_demo_data.py")
    print("  3. Start the application")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
