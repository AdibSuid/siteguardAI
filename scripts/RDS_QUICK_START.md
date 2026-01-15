# AWS RDS PostgreSQL - Quick Start Guide

## Overview
This guide helps you create an AWS RDS PostgreSQL instance for the SiteGuard AI project.

## Prerequisites
- AWS Account (Free Tier eligible)
- Python 3.10+ installed
- pip packages: `psycopg2-binary`, `sqlalchemy`, `python-dotenv`

## Quick Setup (5 Steps)

### Step 1: Get Your Public IP
```bash
python scripts/get_public_ip.py
```
Save this IP - you'll need it for the security group.

### Step 2: Create RDS Instance in AWS Console

**Quick Settings:**
- Engine: PostgreSQL 15
- Template: Free tier
- DB instance identifier: `siteguard-db`
- Master username: `postgres`
- Master password: (create a strong password)
- Instance class: db.t3.micro
- Storage: 20 GB
- Public access: Yes
- Initial database name: `siteguard`
- Automated backups: Enabled (7 days)

**Detailed instructions:** See `scripts/setup_rds.md`

### Step 3: Configure Security Group

After database is created (5-10 minutes):
1. Go to RDS Console → Your database → Connectivity & security
2. Click on the VPC security group
3. Edit inbound rules → Add rule:
   - Type: PostgreSQL
   - Port: 5432
   - Source: Your IP from Step 1
   - Description: Development access

### Step 4: Generate Database Configuration
```bash
python scripts/generate_database_url.py
```
This will prompt you for:
- RDS endpoint (from AWS Console)
- Password (from Step 2)
- Other details (defaults provided)

Copy the output to your `.env` file.

### Step 5: Validate Connection
```bash
python scripts/validate_rds_connection.py
```

If all tests pass, you're ready to proceed! ✓

## What You Created

- **RDS Instance**: PostgreSQL 15 database on AWS
- **Storage**: 20 GB (Free Tier)
- **Backups**: Automated daily backups (7-day retention)
- **Security**: Restricted access from your IP only
- **Cost**: $0 (within Free Tier limits)

## Next Steps

After successful validation:
1. ✓ Task 2 complete - RDS instance created
2. → Task 3: Implement database models
3. → Task 4: Set up Alembic migrations
4. → Task 5: Implement database service layer

## Troubleshooting

### Connection timeout
- Check security group allows your IP
- Verify "Public access" is enabled
- Confirm RDS instance status is "Available"

### Authentication failed
- Verify password is correct
- Check username (default: postgres)
- Ensure database name matches (default: siteguard)

### Cannot find endpoint
- Go to RDS Console
- Click on your database instance
- Look in "Connectivity & security" section
- Copy the "Endpoint" value

## Cost Monitoring

Free Tier includes:
- 750 hours/month of db.t3.micro (enough for 24/7 operation)
- 20 GB storage
- 20 GB backup storage

Set up billing alert:
1. AWS Console → Billing Dashboard
2. Create alert for $1 threshold
3. Monitor usage regularly

## Teardown (After Demo)

When you're done:
```bash
python scripts/teardown_aws.py
```

Or manually:
1. RDS Console → Select database
2. Actions → Delete
3. Uncheck "Create final snapshot"
4. Confirm deletion

## Resources

- Full setup guide: `scripts/setup_rds.md`
- Validation script: `scripts/validate_rds_connection.py`
- IP helper: `scripts/get_public_ip.py`
- URL generator: `scripts/generate_database_url.py`

## Support

If you encounter issues:
1. Check AWS RDS service health
2. Review security group configuration
3. Verify your IP hasn't changed
4. Check AWS Free Tier usage limits
5. See troubleshooting section in `scripts/setup_rds.md`
