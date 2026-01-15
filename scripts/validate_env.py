#!/usr/bin/env python3
"""
Environment Variable Validation Script
Validates that all required environment variables are set for AWS Database & Auth Integration
"""

import os
import sys
from typing import List, Dict, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define required environment variables by category
REQUIRED_ENV_VARS = {
    "Database Configuration": [
        "DATABASE_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ],
    "AWS Configuration": [
        "AWS_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ],
    "Microsoft Azure AD B2C": [
        "AZURE_AD_TENANT_ID",
        "AZURE_AD_CLIENT_ID",
        "AZURE_AD_CLIENT_SECRET",
        "AZURE_AD_REDIRECT_URI",
    ],
    "JWT & Security": [
        "SECRET_KEY",
        "SESSION_SECRET_KEY",
    ],
}

# Optional environment variables with defaults
OPTIONAL_ENV_VARS = {
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "DB_POOL_SIZE": "10",
    "DB_MAX_OVERFLOW": "20",
    "AZURE_AD_AUTHORITY": None,  # Can be constructed from TENANT_ID
}


def validate_environment() -> Tuple[bool, List[str], List[str]]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Tuple of (is_valid, missing_vars, warnings)
    """
    missing_vars = []
    warnings = []
    
    # Check required variables
    for category, vars_list in REQUIRED_ENV_VARS.items():
        for var in vars_list:
            value = os.getenv(var)
            if not value:
                missing_vars.append(f"{var} ({category})")
            elif value.startswith("your_") or value == "your-secret-key-change-in-production-use-long-random-string":
                warnings.append(f"{var} appears to be using placeholder value")
    
    # Check optional variables and provide info
    for var, default in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var)
        if not value and default:
            warnings.append(f"{var} not set, will use default: {default}")
    
    # Validate DATABASE_URL format
    db_url = os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("postgresql://"):
        warnings.append("DATABASE_URL should start with 'postgresql://'")
    
    # Validate SECRET_KEY length
    secret_key = os.getenv("SECRET_KEY")
    if secret_key and len(secret_key) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters long for security")
    
    is_valid = len(missing_vars) == 0
    return is_valid, missing_vars, warnings


def print_validation_results(is_valid: bool, missing_vars: List[str], warnings: List[str]):
    """Print validation results in a formatted way"""
    
    print("\n" + "="*70)
    print("  ENVIRONMENT VARIABLE VALIDATION")
    print("="*70 + "\n")
    
    if is_valid:
        print("✅ SUCCESS: All required environment variables are set!\n")
    else:
        print("❌ FAILURE: Missing required environment variables!\n")
        print("Missing Variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not is_valid:
        print("📝 ACTION REQUIRED:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in all required values in .env")
        print("  3. Run this script again to validate")
        print()
    
    print("="*70 + "\n")


def main():
    """Main validation function"""
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n❌ ERROR: .env file not found!")
        print("\n📝 ACTION REQUIRED:")
        print("  1. Copy .env.example to .env:")
        print("     cp .env.example .env")
        print("  2. Edit .env and fill in your values")
        print("  3. Run this script again\n")
        sys.exit(1)
    
    # Validate environment variables
    is_valid, missing_vars, warnings = validate_environment()
    
    # Print results
    print_validation_results(is_valid, missing_vars, warnings)
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
