# AWS RDS Setup Scripts

This directory contains scripts and documentation to help you set up AWS RDS PostgreSQL for the SiteGuard AI project.

## Quick Start

**New to AWS RDS?** Start here:
1. Read: `RDS_QUICK_START.md` (5-minute overview)
2. Follow: `task2_checklist.md` (step-by-step checklist)
3. Validate: Run `python validate_rds_connection.py`

**Need detailed instructions?** See `setup_rds.md`

## Files Overview

### Documentation

| File | Purpose | When to Use |
|------|---------|-------------|
| `RDS_QUICK_START.md` | Quick 5-step setup guide | First time setup |
| `setup_rds.md` | Detailed AWS Console walkthrough | Need detailed instructions |
| `task2_checklist.md` | Interactive checklist | Track your progress |
| `README_RDS_SETUP.md` | This file | Overview of all resources |

### Python Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `get_public_ip.py` | Get your public IP for security group | `python scripts/get_public_ip.py` |
| `generate_database_url.py` | Generate DATABASE_URL from RDS details | `python scripts/generate_database_url.py` |
| `validate_rds_connection.py` | Test database connectivity | `python scripts/validate_rds_connection.py` |

## Workflow

```
1. Get Public IP
   └─> python scripts/get_public_ip.py
       └─> Note IP address

2. Create RDS Instance
   └─> Follow RDS_QUICK_START.md or setup_rds.md
       └─> Use task2_checklist.md to track progress
           └─> Wait for "Available" status

3. Configure Security Group
   └─> Add inbound rule for your IP
       └─> Port 5432, PostgreSQL

4. Generate Configuration
   └─> python scripts/generate_database_url.py
       └─> Copy output to .env file

5. Validate Connection
   └─> python scripts/validate_rds_connection.py
       └─> All tests should pass ✓
```

## Prerequisites

### AWS Account
- Active AWS account
- Free Tier eligible (recommended)
- Access to AWS Console

### Python Environment
```bash
pip install psycopg2-binary sqlalchemy python-dotenv requests
```

### Environment File
Copy `.env.example` to `.env` and fill in RDS details after creation.

## What Gets Created

When you complete the setup:

### AWS Resources
- **RDS Instance**: PostgreSQL 15 database
- **Storage**: 20 GB General Purpose SSD
- **Backups**: Automated daily backups (7-day retention)
- **Security Group**: Restricts access to your IP only
- **Instance Type**: db.t3.micro (Free Tier eligible)

### Local Configuration
- `.env` file with database credentials
- Validated database connection
- Ready for Alembic migrations

## Cost Information

**Free Tier Limits:**
- 750 hours/month of db.t3.micro
- 20 GB storage
- 20 GB backup storage

**Expected Cost:** $0 (within Free Tier)

**Recommendation:** Set up billing alert for $1 in AWS Console

## Validation

After setup, run validation:

```bash
python scripts/validate_rds_connection.py
```

**Expected output:**
```
✓ psycopg2 is installed
✓ SQLAlchemy is installed
✓ All environment variables set
✓ Successfully connected to database
✓ PostgreSQL version: PostgreSQL 15.x
✓ Connected to database: siteguard
✓ SQLAlchemy connection successful
✓ All validation tests passed!
```

## Troubleshooting

### Connection Timeout
**Cause:** Security group not configured or public access disabled  
**Fix:** 
1. Check security group allows your IP on port 5432
2. Verify "Public access" is enabled on RDS instance
3. Confirm instance status is "Available"

### Authentication Failed
**Cause:** Incorrect credentials  
**Fix:**
1. Verify password in .env matches RDS master password
2. Check username (default: postgres)
3. Ensure database name matches (default: siteguard)

### Cannot Find Endpoint
**Cause:** Looking in wrong place  
**Fix:**
1. Go to RDS Console
2. Click your database instance
3. Look in "Connectivity & security" section
4. Copy the "Endpoint" value

### IP Changed
**Cause:** Dynamic IP address changed  
**Fix:**
1. Run `python scripts/get_public_ip.py` to get new IP
2. Update security group inbound rule with new IP

## Next Steps

After successful validation:

1. ✓ Task 2 complete
2. → Task 3: Implement database models (`app/core/database/models.py`)
3. → Task 4: Set up Alembic migrations
4. → Task 5: Implement database service layer

## Teardown

When you're done with the demo:

### Option 1: Use Script (Coming Soon)
```bash
python scripts/teardown_aws.py
```

### Option 2: Manual Deletion
1. Go to RDS Console
2. Select your database instance
3. Actions → Delete
4. Uncheck "Create final snapshot"
5. Check "I acknowledge..."
6. Type "delete me"
7. Click "Delete"

**Important:** Verify deletion to avoid charges

## Support

### Documentation
- AWS RDS Free Tier: https://aws.amazon.com/rds/free/
- PostgreSQL on RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- RDS Security Groups: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html

### Project Documentation
- Requirements: `.kiro/specs/aws-database-auth/requirements.md`
- Design: `.kiro/specs/aws-database-auth/design.md`
- Tasks: `.kiro/specs/aws-database-auth/tasks.md`

### Getting Help
1. Check troubleshooting section above
2. Review `setup_rds.md` for detailed instructions
3. Verify AWS service health status
4. Check AWS Free Tier usage limits

## Script Details

### get_public_ip.py
Retrieves your public IP address using AWS's checkip service.

**Usage:**
```bash
python scripts/get_public_ip.py
```

**Output:**
```
Your public IP address: 203.0.113.42
Use this IP when configuring AWS RDS security group:
  Source: 203.0.113.42/32
  Type: PostgreSQL
  Port: 5432
```

### generate_database_url.py
Interactive script to generate DATABASE_URL and related environment variables.

**Usage:**
```bash
python scripts/generate_database_url.py
```

**Prompts for:**
- RDS endpoint
- Port (default: 5432)
- Database name (default: siteguard)
- Username (default: postgres)
- Password

**Output:**
```
DATABASE_URL=postgresql://postgres:password@endpoint:5432/siteguard
DB_HOST=endpoint
DB_PORT=5432
DB_NAME=siteguard
DB_USER=postgres
DB_PASSWORD=password
```

### validate_rds_connection.py
Comprehensive validation of database connectivity and configuration.

**Usage:**
```bash
python scripts/validate_rds_connection.py
```

**Tests:**
1. Python packages installed (psycopg2, SQLAlchemy)
2. Environment variables configured
3. Database connection successful
4. PostgreSQL version check
5. SQLAlchemy connection test
6. Table listing (if any exist)

**Exit codes:**
- 0: All tests passed
- 1: One or more tests failed

## Tips

### Security Best Practices
- Use strong passwords (16+ characters, mixed case, numbers, symbols)
- Restrict security group to your IP only
- Enable encryption at rest (included in setup)
- Don't commit .env file to version control
- Rotate passwords regularly

### Performance Tips
- Use connection pooling (configured in DatabaseManager)
- Add indexes on frequently queried columns
- Monitor slow queries (>1 second)
- Use EXPLAIN ANALYZE for query optimization

### Cost Optimization
- Stay within Free Tier limits (750 hours/month)
- Delete instance when not in use (for demo only)
- Monitor storage usage (20 GB limit)
- Set up billing alerts

## Version History

- **v1.0** (2026-01-14): Initial release
  - RDS setup documentation
  - Helper scripts for IP, URL generation, validation
  - Interactive checklist
  - Troubleshooting guide

## License

Part of the SiteGuard AI project. See main LICENSE file.
