#!/usr/bin/env python3
"""
Create the siteguard database in MySQL RDS
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

database_name = "siteguard"

print("=" * 60)
print("Create MySQL Database")
print("=" * 60)
print(f"\nConnecting to: {host}:{port}")
print(f"Username: {username}")
print(f"Database to create: {database_name}")
print()

try:
    # Connect WITHOUT specifying a database
    conn = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        connect_timeout=10
    )
    
    print("✓ Connected successfully!")
    
    cursor = conn.cursor()
    
    # Check if database already exists
    cursor.execute("SHOW DATABASES;")
    databases = [db[0] for db in cursor.fetchall()]
    
    if database_name in databases:
        print(f"✓ Database '{database_name}' already exists!")
    else:
        # Create database
        print(f"\nCreating database '{database_name}'...")
        cursor.execute(f"CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"✓ Database '{database_name}' created successfully!")
    
    # Verify it was created
    cursor.execute("SHOW DATABASES;")
    databases = [db[0] for db in cursor.fetchall()]
    
    if database_name in databases:
        print(f"✓ Verified: Database '{database_name}' exists")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 60)
    print("Next Steps")
    print("=" * 60)
    print(f"\nUpdate your .env file with:")
    print(f"\n  DB_NAME={database_name}")
    
    # Generate DATABASE_URL with proper encoding
    encoded_password = password.replace('#', '%23').replace('@', '%40').replace('&', '%26')
    print(f"  DATABASE_URL=mysql+pymysql://{username}:{encoded_password}@{host}:{port}/{database_name}")
    
    print(f"\nThen run:")
    print(f"  python scripts/validate_mysql_connection.py")
    print()
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Verify username and password are correct")
    print("  2. Check user has CREATE DATABASE permission")
    print("  3. Verify RDS instance is 'Available'")
