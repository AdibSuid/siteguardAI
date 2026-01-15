# Fix: MySQL/Aurora to PostgreSQL Migration

## Issue
You created a MySQL/Aurora RDS instance instead of PostgreSQL.

## Why PostgreSQL is Required
- The project uses PostgreSQL-specific features
- SQLAlchemy models are designed for PostgreSQL
- Alembic migrations are configured for PostgreSQL
- The design document specifies PostgreSQL 15

## Solution: Create New PostgreSQL Instance

### Step 1: Delete MySQL/Aurora Instance (Optional)

To avoid confusion and stay within Free Tier:

1. Go to AWS RDS Console
2. Select your MySQL instance: `siteguard-db`
3. Actions → Delete
4. Uncheck "Create final snapshot"
5. Check "I acknowledge..."
6. Type "delete me"
7. Click Delete

### Step 2: Create PostgreSQL Instance

Follow the guide with these **CRITICAL** settings:

**Engine Selection:**
- ✓ Engine type: **PostgreSQL** (NOT MySQL/Aurora)
- ✓ Version: PostgreSQL 15.x
- ✓ Template: Free tier

**Instance Configuration:**
- DB instance identifier: `siteguard-db-postgres`
- Master username: `postgres`
- Master password: (your choice - save it!)
- Instance class: db.t3.micro
- Storage: 20 GB

**Connectivity:**
- Public access: **Yes**
- VPC security group: Create new
- Security group name: `siteguard-postgres-sg`

**Database Options:**
- Initial database name: `siteguard`
- Port: **5432** (PostgreSQL default)

**Backup:**
- Enable automated backups: Yes
- Retention period: 7 days

### Step 3: Configure Security Group

After instance is created:

1. Go to RDS Console → Your PostgreSQL instance
2. Click on VPC security group
3. Edit inbound rules → Add rule:
   - Type: **PostgreSQL**
   - Port: **5432**
   - Source: `42.190.91.98/32` (your IP)
   - Description: Development access

### Step 4: Update .env File

Your DATABASE_URL should look like this:

```bash
# PostgreSQL Configuration (NOT MySQL)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@siteguard-db-postgres.cela8keww4th.us-east-1.rds.amazonaws.com:5432/siteguard
DB_HOST=siteguard-db-postgres.cela8keww4th.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=siteguard
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
```

**Key differences from MySQL:**
- Protocol: `postgresql://` (not `mysql://`)
- Port: `5432` (not `3306`)
- Default user: `postgres` (not `siteguard`)
- Default database: `siteguard` (not `siteguard-db`)

### Step 5: Validate Connection

```bash
python scripts/validate_rds_connection.py
```

Expected output:
```
✓ Successfully connected to database
✓ PostgreSQL version: PostgreSQL 15.x
```

## Alternative: Use Existing MySQL (Not Recommended)

If you want to keep MySQL, you would need to:
1. Change all project code to use MySQL instead of PostgreSQL
2. Update SQLAlchemy models for MySQL compatibility
3. Change Alembic migrations for MySQL
4. Install MySQL driver: `pip install pymysql`
5. Update DATABASE_URL to use `mysql+pymysql://`

**This is NOT recommended** because:
- Requires significant code changes
- PostgreSQL is specified in requirements
- May have compatibility issues
- Not part of the original design

## Recommended Action

**Create a new PostgreSQL RDS instance** following the guide in `scripts/setup_rds.md`, making sure to select:
- Engine: **PostgreSQL** (not MySQL/Aurora)
- Port: **5432**
- Template: Free tier

This will ensure compatibility with the rest of the project.
