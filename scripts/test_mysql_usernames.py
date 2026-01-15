#!/usr/bin/env python3
"""
Test different MySQL usernames to find the correct one
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Get connection details from .env
host = os.getenv("DB_HOST")
port = int(os.getenv("DB_PORT"))
database = os.getenv("DB_NAME")
password = os.getenv("DB_PASSWORD")

# Common MySQL master usernames
usernames_to_try = [
    "admin",      # Default for Aurora/RDS MySQL
    "root",       # Common MySQL username
    "siteguard",  # Your current username
    "postgres",   # Sometimes people use this by mistake
    "mysql",      # Another common one
]

print("=" * 60)
print("Testing MySQL Usernames")
print("=" * 60)
print(f"\nHost: {host}")
print(f"Port: {port}")
print(f"Database: {database}")
print(f"Password: {'*' * len(password)}")
print("\nTrying different usernames...\n")

successful_username = None

for username in usernames_to_try:
    try:
        print(f"Testing username: '{username}'...", end=" ")
        conn = pymysql.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            connect_timeout=5
        )
        print("✓ SUCCESS!")
        successful_username = username
        
        # Get some info
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()[0]
        print(f"  MySQL version: {version}")
        
        cursor.execute("SELECT USER();")
        current_user = cursor.fetchone()[0]
        print(f"  Connected as: {current_user}")
        
        cursor.close()
        conn.close()
        break
        
    except pymysql.err.OperationalError as e:
        if "Access denied" in str(e):
            print("✗ Access denied")
        else:
            print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 60)

if successful_username:
    print(f"✓ Found working username: '{successful_username}'")
    print("=" * 60)
    print("\nUpdate your .env file with:")
    print(f"\nDB_USER={successful_username}")
    print(f"DATABASE_URL=mysql+pymysql://{successful_username}:{password.replace('#', '%23')}@{host}:{port}/{database}")
    print("\nThen run: python scripts/validate_mysql_connection.py")
else:
    print("✗ No working username found")
    print("=" * 60)
    print("\nPossible issues:")
    print("  1. Password is incorrect")
    print("  2. Master username is different from common ones")
    print("\nSolutions:")
    print("  1. Check AWS RDS Console → Your database → Configuration tab")
    print("     Look for 'Master username'")
    print("  2. Reset password in AWS Console if needed")
    print("  3. See: scripts/FIX_AUTHENTICATION.md")
