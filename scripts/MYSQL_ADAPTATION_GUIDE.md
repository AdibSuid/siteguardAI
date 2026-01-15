# MySQL Adaptation Guide

## Overview

You've chosen to use MySQL/Aurora instead of PostgreSQL. This guide covers the necessary changes to adapt the project.

## Current Configuration

Your MySQL RDS instance:
- Endpoint: `siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com`
- Port: 3306
- Database: `siteguard-db`
- User: `siteguard`
- Password: `AhmadSpiderman67#`

## Required Changes

### 1. Fix DATABASE_URL Format

Your current `.env` has a small issue. Update it to:

```bash
# Database Configuration (AWS RDS MySQL)
DATABASE_URL=mysql+pymysql://siteguard:AhmadSpiderman67%23@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_HOST=siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=siteguard-db
DB_USER=siteguard
DB_PASSWORD=AhmadSpiderman67#
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

**Key changes:**
- Protocol: `mysql+pymysql://` (not just `mysql://`)
- Password: `AhmadSpiderman67%23` (URL-encoded `#` as `%23`)

### 2. Install MySQL Driver

```bash
pip install pymysql cryptography
```

### 3. Fix Security Group

The connection timeout suggests your security group isn't configured correctly.

**Steps:**
1. Go to AWS RDS Console
2. Click on your database: `siteguard-db`
3. Go to "Connectivity & security" tab
4. Click on the VPC security group link
5. Click "Edit inbound rules"
6. Add rule:
   - Type: **MYSQL/Aurora**
   - Port: **3306**
   - Source: **My IP** or `42.190.91.98/32`
   - Description: Development access
7. Click "Save rules"

### 4. Update SQLAlchemy Models

MySQL has some differences from PostgreSQL. The main changes needed:

**File: `app/core/database/models.py`**

Changes needed:
- Use `String` instead of `Text` for some fields (MySQL has length limits)
- Use `CHAR(36)` for UUIDs instead of UUID type
- Adjust JSON column handling

### 5. Update Alembic Configuration

Alembic migrations will need to target MySQL instead of PostgreSQL.

## Differences: MySQL vs PostgreSQL

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| UUID Type | Native UUID | CHAR(36) or BINARY(16) |
| JSON Type | Native JSONB | JSON (less features) |
| Text Fields | Unlimited TEXT | VARCHAR(max) or TEXT |
| Port | 5432 | 3306 |
| Driver | psycopg2 | pymysql |
| URL Prefix | postgresql:// | mysql+pymysql:// |

## Testing Connection

After fixing security group and installing pymysql, test:

```bash
python scripts/validate_mysql_connection.py
```

## Next Steps

1. Fix security group (most likely cause of timeout)
2. Install pymysql: `pip install pymysql cryptography`
3. Update DATABASE_URL in .env
4. Test connection
5. Adapt database models for MySQL compatibility
