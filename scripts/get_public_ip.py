#!/usr/bin/env python3
"""
Get your public IP address for AWS security group configuration
"""

import requests
import sys

def get_public_ip():
    """Get public IP address"""
    try:
        response = requests.get('https://checkip.amazonaws.com', timeout=5)
        response.raise_for_status()
        ip = response.text.strip()
        return ip
    except Exception as e:
        print(f"Error getting public IP: {e}")
        print("\nAlternative methods:")
        print("  1. Visit: https://whatismyipaddress.com/")
        print("  2. Run: curl https://checkip.amazonaws.com")
        return None

def main():
    print("=" * 60)
    print("Getting Your Public IP Address")
    print("=" * 60)
    
    ip = get_public_ip()
    
    if ip:
        print(f"\n✓ Your public IP address: {ip}")
        print("\nUse this IP when configuring AWS RDS security group:")
        print(f"  Source: {ip}/32")
        print(f"  Type: PostgreSQL")
        print(f"  Port: 5432")
        print("\nNote: If you have a dynamic IP, you may need to update")
        print("      the security group when your IP changes.")
    else:
        print("\n✗ Could not determine public IP address")
        sys.exit(1)

if __name__ == "__main__":
    main()
