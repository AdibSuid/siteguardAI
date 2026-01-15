#!/usr/bin/env python3
"""
Generate DATABASE_URL for MySQL from RDS connection details
"""

import sys
from urllib.parse import quote_plus

def generate_mysql_url():
    """Interactive script to generate MySQL DATABASE_URL"""
    print("=" * 60)
    print("Generate DATABASE_URL for AWS RDS MySQL")
    print("=" * 60)
    
    print("\nEnter your RDS connection details:")
    print("(You can find these in the AWS RDS Console)")
    print()
    
    # Get inputs with defaults
    endpoint = input("RDS Endpoint: ").strip()
    if not endpoint:
        print("\n✗ Endpoint is required!")
        sys.exit(1)
    
    port = input("Port [3306]: ").strip() or "3306"
    database = input("Database name: ").strip()
    if not database:
        print("\n✗ Database name is required!")
        sys.exit(1)
    
    username = input("Master username: ").strip()
    if not username:
        print("\n✗ Username is required!")
        sys.exit(1)
    
    password = input("Master password: ").strip()
    if not password:
        print("\n✗ Password is required!")
        sys.exit(1)
    
    # URL encode password to handle special characters
    encoded_password = quote_plus(password)
    
    # Generate DATABASE_URL for MySQL
    database_url = f"mysql+pymysql://{username}:{encoded_password}@{endpoint}:{port}/{database}"
    
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
    
    # Show special character encoding info
    if password != encoded_password:
        print("Note: Password contains special characters.")
        print(f"  Original: {password}")
        print(f"  URL-encoded: {encoded_password}")
        print()
    
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Copy the above variables to your .env file")
    print("  2. Run: python scripts/validate_mysql_connection.py")
    print("  3. If connection succeeds, Task 2 is complete!")

if __name__ == "__main__":
    try:
        generate_mysql_url()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
