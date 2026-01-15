# Task 2: MySQL RDS Setup - Current Status

## Overview

You've chosen to use **MySQL/Aurora** instead of PostgreSQL. The database instance is created, but the **security group needs to be configured** to allow connections.

## Current Status

### ✓ Completed
- [x] MySQL RDS instance created
- [x] Endpoint obtained: `siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com`
- [x] `.env` file updated with correct MySQL format
- [x] pymysql driver installed
- [x] requirements.txt updated
- [x] Security group configured (connection no longer times out)

### ⚠ Needs Attention
- [ ] **Authentication credentials** (CRITICAL - username or password incorrect)
- [ ] Verify master username in AWS Console
- [ ] Reset password if needed
- [ ] Connection validation

### → Next Steps
- [ ] Adapt database models for MySQL
- [ ] Update Alembic migrations for MySQL
- [ ] Test full database integration

## Current Configuration

### Database Details
```
Engine:   MySQL/Aurora
Endpoint: siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com
Port:     3306
Database: siteguard-db
User:     siteguard
Password: AhmadSpiderman67#
```

### .env Configuration
```bash
DATABASE_URL=mysql+pymysql://siteguard:AhmadSpiderman67%23@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_HOST=siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=siteguard-db
DB_USER=siteguard
DB_PASSWORD=AhmadSpiderman67#
```

### Your IP Address
```
42.190.91.98
```

## CRITICAL: Fix Authentication

The connection reaches the database (security group is working!), but authentication is failing:

```
Access denied for user 'siteguard'@'42.190.91.98' (using password: YES)
```

This means the username or password is incorrect.

### Quick Fix Steps

**Follow this guide:** `scripts/CHECK_RDS_CREDENTIALS.md`

**Quick steps:**

1. **Check Master Username in AWS Console**
   - Go to RDS Console → Your database → Configuration tab
   - Find "Master username" (might be 'admin', 'root', or something else)
   - Write it down

2. **Reset Password (Recommended)**
   - Click "Modify" button
   - Check "New master password"
   - Enter new password (e.g., `SiteGuard2026Secure`)
   - Apply immediately
   - Wait 2-3 minutes

3. **Update .env File**
   ```bash
   DB_USER=<master_username_from_step_1>
   DB_PASSWORD=<new_password_from_step_2>
   DATABASE_URL=mysql+pymysql://<username>:<password>@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
   ```

4. **Test Connection**
   ```bash
   python scripts/validate_mysql_connection.py
   ```

**Detailed instructions:** See `scripts/CHECK_RDS_CREDENTIALS.md`

## Validation

After fixing the security group, run:

```bash
python scripts/validate_mysql_connection.py
```

**Expected output:**
```
✓ pymysql is installed
✓ SQLAlchemy is installed
✓ All environment variables set
✓ Successfully connected to database
✓ MySQL version: 8.0.x
✓ Connected to database: siteguard-db
✓ All validation tests passed!
```

## MySQL vs PostgreSQL Adaptations

Since you're using MySQL instead of the originally planned PostgreSQL, some code adaptations will be needed:

### Database Models (Task 3)
- Use `String(36)` for UUIDs instead of `UUID` type
- Use `String(length)` instead of unlimited `Text` in some cases
- JSON handling differences

### Alembic Migrations (Task 4)
- Target MySQL dialect instead of PostgreSQL
- Different index syntax
- Different constraint syntax

### SQLAlchemy Connection (Task 3)
- Already configured with `mysql+pymysql://` protocol
- Connection pooling works the same

## Files Created

### Documentation
- `scripts/MYSQL_ADAPTATION_GUIDE.md` - Overview of MySQL changes
- `scripts/FIX_SECURITY_GROUP.md` - Detailed security group fix guide
- `TASK_2_MYSQL_STATUS.md` - This file

### Scripts
- `scripts/validate_mysql_connection.py` - MySQL-specific validation

### Configuration
- `.env` - Updated with correct MySQL format
- `requirements.txt` - Added pymysql>=1.1.0

## Next Actions

### Immediate (Required)
1. **Fix security group** - Follow `scripts/FIX_SECURITY_GROUP.md`
2. **Validate connection** - Run `python scripts/validate_mysql_connection.py`
3. **Mark Task 2 complete** - Once validation passes

### After Task 2
1. **Task 3**: Implement database models (adapt for MySQL)
2. **Task 4**: Set up Alembic migrations (configure for MySQL)
3. **Task 5**: Implement database service layer

## Troubleshooting

### Connection Timeout
**Cause:** Security group not configured  
**Fix:** Follow `scripts/FIX_SECURITY_GROUP.md`

### Authentication Failed
**Cause:** Wrong credentials  
**Fix:** Verify password in .env matches RDS

### Wrong Port
**Cause:** Using PostgreSQL port (5432) instead of MySQL (3306)  
**Fix:** Already corrected in .env

### Wrong Protocol
**Cause:** Using `mysql://` instead of `mysql+pymysql://`  
**Fix:** Already corrected in .env

## Cost Information

**MySQL RDS Free Tier:**
- 750 hours/month of db.t3.micro (or db.t2.micro)
- 20 GB storage
- 20 GB backup storage
- **Expected cost: $0** (within free tier)

## Support Resources

### Documentation
- `scripts/FIX_SECURITY_GROUP.md` - Security group configuration
- `scripts/MYSQL_ADAPTATION_GUIDE.md` - MySQL-specific changes
- `scripts/README_RDS_SETUP.md` - General RDS setup guide

### Scripts
- `scripts/get_public_ip.py` - Get your current IP
- `scripts/validate_mysql_connection.py` - Test MySQL connection
- `scripts/check_rds_prerequisites.py` - Verify prerequisites

### AWS Console
- RDS: https://console.aws.amazon.com/rds/
- EC2 Security Groups: https://console.aws.amazon.com/ec2/

## Summary

**Current blocker:** Security group not configured for MySQL port 3306

**Solution:** Add inbound rule allowing your IP (42.190.91.98/32) on port 3306

**Time to fix:** 2-3 minutes

**After fix:** Task 2 will be complete and you can proceed to Task 3

---

**Action Required:** Configure security group following `scripts/FIX_SECURITY_GROUP.md`
