#!/usr/bin/env python3
"""
Generate DATABASE_URL from RDS connection details
"""

import sys
from urllib.parse import quote_plus

def generate_database_url():
    """Interactive script to generate DATABASE_URL"""
    print("=" * 60)
    print("Generate DATABASE_URL for AWS RDS PostgreSQL")
    print("=" * 60)
    
    print("\nEnter your RDS connection details:")
    print("(You can find these in the AWS RDS Console)")
    print()
    
    # Get inputs
    endpoint = input("RDS Endpoint (e.g., siteguard-db.xxxxx.us-east-1.rds.amazonaws.com): ").strip()
    port = input("Port [5432]: ").strip() or "5432"
    database = input("Database name [siteguard]: ").strip() or "siteguard"
    username = input("Username [postgres]: ").strip() or "postgres"
    password = input("Password: ").strip()
    
    if not endpoint or not password:
        print("\n✗ Endpoint and password are required!")
        sys.exit(1)
    
    # URL encode password to handle special characters
    encoded_password = quote_plus(password)
    
    # Generate DATABASE_URL
    database_url = f"postgresql://{username}:{encoded_password}@{endpoint}:{port}/{database}"
    
    print("\n" + "=" * 60)
    print("Generated Configuration")
    print("=" * 60)
    
    print("\nAdd these to your .env file:")
    print()
    print(f"DATABASE_URL={database_url}")
    print(f"DB_HOST={endpoint}")
    print(f"DB_PORT={port}")
    print(f"DB_NAME={database}")
    print(f"DB_USER={username}")
    print(f"DB_PASSWORD={password}")
    print()
    
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Copy the above variables to your .env file")
    print("  2. Run: python scripts/validate_rds_connection.py")
    print("  3. If connection succeeds, proceed with database migrations")

if __name__ == "__main__":
    try:
        generate_database_url()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
