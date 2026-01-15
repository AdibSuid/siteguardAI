#!/usr/bin/env python3
"""
List all databases in MySQL RDS instance
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

print("=" * 60)
print("List MySQL Databases")
print("=" * 60)
print(f"\nConnecting to: {host}:{port}")
print(f"Username: {username}")
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
    print()
    
    cursor = conn.cursor()
    
    # List all databases
    cursor.execute("SHOW DATABASES;")
    databases = cursor.fetchall()
    
    print("Available databases:")
    print("-" * 60)
    for db in databases:
        db_name = db[0]
        # Skip system databases
        if db_name not in ['information_schema', 'mysql', 'performance_schema', 'sys']:
            print(f"  ✓ {db_name}")
        else:
            print(f"    {db_name} (system database)")
    
    print()
    print("=" * 60)
    print("Solution:")
    print("=" * 60)
    
    # Find user databases
    user_dbs = [db[0] for db in databases if db[0] not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
    
    if user_dbs:
        print(f"\nUse one of these databases in your .env file:")
        for db_name in user_dbs:
            print(f"\n  DB_NAME={db_name}")
            print(f"  DATABASE_URL=mysql+pymysql://{username}:{password.replace('#', '%23')}@{host}:{port}/{db_name}")
    else:
        print("\n✗ No user databases found!")
        print("\nYou need to create a database. Run this command:")
        print(f"\n  CREATE DATABASE siteguard;")
        print("\nOr use the script: python scripts/create_mysql_database.py")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Verify username and password are correct")
    print("  2. Check security group allows your IP")
    print("  3. Verify RDS instance is 'Available'")
