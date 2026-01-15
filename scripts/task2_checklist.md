# Task 2: Create AWS RDS PostgreSQL Instance - Checklist

Use this checklist to track your progress through Task 2.

## Pre-Setup

- [ ] AWS Account created and accessible
- [ ] AWS Free Tier eligible (within 12 months of signup)
- [ ] Python 3.10+ installed
- [ ] Required packages installed: `pip install psycopg2-binary sqlalchemy python-dotenv requests`

## Step 1: Get Public IP

- [ ] Run: `python scripts/get_public_ip.py`
- [ ] Note your public IP: `___________________________`

## Step 2: Create RDS Instance in AWS Console

- [ ] Log into AWS Console
- [ ] Navigate to RDS service
- [ ] Click "Create database"

### Engine Configuration
- [ ] Engine type: PostgreSQL
- [ ] Version: PostgreSQL 15.x
- [ ] Template: Free tier

### Instance Settings
- [ ] DB instance identifier: `siteguard-db` (or your choice)
- [ ] Master username: `postgres`
- [ ] Master password created: `___________________________` (save securely!)
- [ ] Password confirmed

### Instance Specifications
- [ ] Instance class: db.t3.micro
- [ ] Storage type: General Purpose SSD (gp2)
- [ ] Allocated storage: 20 GB
- [ ] Storage autoscaling: Disabled

### Connectivity
- [ ] Public access: Yes
- [ ] VPC security group: Create new
- [ ] Security group name: `siteguard-db-sg`

### Database Options
- [ ] Initial database name: `siteguard`
- [ ] DB parameter group: default.postgres15

### Backup Configuration
- [ ] Enable automated backups: Yes
- [ ] Backup retention period: 7 days
- [ ] Copy tags to snapshots: Yes

### Additional Settings
- [ ] Enable encryption: Yes
- [ ] Enable Enhanced monitoring: No (to stay in free tier)
- [ ] Enable auto minor version upgrade: Yes
- [ ] Enable deletion protection: No (for easy teardown)

### Create Database
- [ ] Review all settings
- [ ] Click "Create database"
- [ ] Wait for status to change to "Available" (5-10 minutes)
- [ ] Database endpoint noted: `___________________________`

## Step 3: Configure Security Group

- [ ] Click on database instance name
- [ ] Navigate to "Connectivity & security" section
- [ ] Click on VPC security group link
- [ ] Click "Edit inbound rules"
- [ ] Click "Add rule"
- [ ] Type: PostgreSQL
- [ ] Protocol: TCP
- [ ] Port: 5432
- [ ] Source: My IP (or paste IP from Step 1)
- [ ] Description: Development access
- [ ] Click "Save rules"

## Step 4: Generate Database Configuration

- [ ] Run: `python scripts/generate_database_url.py`
- [ ] Enter RDS endpoint from AWS Console
- [ ] Enter port: 5432
- [ ] Enter database name: siteguard
- [ ] Enter username: postgres
- [ ] Enter password from Step 2
- [ ] Copy generated configuration to `.env` file

### Verify .env File Contains:
- [ ] DATABASE_URL=postgresql://...
- [ ] DB_HOST=your-endpoint.rds.amazonaws.com
- [ ] DB_PORT=5432
- [ ] DB_NAME=siteguard
- [ ] DB_USER=postgres
- [ ] DB_PASSWORD=your-password

## Step 5: Validate Connection

- [ ] Run: `python scripts/validate_rds_connection.py`
- [ ] ✓ psycopg2 is installed
- [ ] ✓ SQLAlchemy is installed
- [ ] ✓ All environment variables set
- [ ] ✓ Database connection successful
- [ ] ✓ PostgreSQL version displayed
- [ ] ✓ Connected to correct database
- [ ] ✓ SQLAlchemy connection successful

## Post-Setup

- [ ] Set up AWS billing alert for $1
- [ ] Document RDS endpoint in team notes
- [ ] Verify database is accessible from development machine
- [ ] Mark Task 2 as complete in tasks.md

## Verification

All checks passed? Run this final verification:

```bash
python scripts/validate_rds_connection.py
```

Expected output:
```
✓ All validation tests passed!
Your RDS PostgreSQL database is ready to use.
```

## Task Complete! ✓

When all items are checked:
- [ ] Task 2 is complete
- [ ] Ready to proceed to Task 3: Implement database models
- [ ] Database is ready for Alembic migrations
- [ ] Connection validated and working

## Troubleshooting

If any step fails, see:
- `scripts/setup_rds.md` - Detailed instructions
- `scripts/RDS_QUICK_START.md` - Quick reference
- `TASK_2_IMPLEMENTATION_SUMMARY.md` - Troubleshooting section

## Time Tracking

- Start time: `___________________________`
- End time: `___________________________`
- Total time: `___________________________`
- AWS provisioning time: ~5-10 minutes
- Configuration time: ~5-10 minutes
- Expected total: ~15-20 minutes

## Notes

Add any notes or issues encountered:

```
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
```

## Next Task

After completion, proceed to:
- **Task 3**: Implement database models and connection management
  - File: `app/core/database/models.py`
  - File: `app/core/database/connection.py`
