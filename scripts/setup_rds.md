# AWS RDS PostgreSQL Setup Guide

## Prerequisites
- AWS Account with Free Tier eligibility
- AWS CLI installed and configured (optional but recommended)
- Your development machine's public IP address

## Step-by-Step Instructions

### Step 1: Get Your Development IP Address

Run this command to get your public IP:
```bash
curl -s https://checkip.amazonaws.com
```

Note this IP address - you'll need it for the security group configuration.

### Step 2: Log into AWS Console

1. Go to https://console.aws.amazon.com/
2. Sign in with your AWS account credentials
3. Ensure you're in your preferred region (e.g., us-east-1)

### Step 3: Navigate to RDS Service

1. In the AWS Console search bar, type "RDS"
2. Click on "RDS" under Services
3. Click "Create database" button

### Step 4: Configure Database Settings

#### Engine Options
- **Engine type**: PostgreSQL
- **Version**: PostgreSQL 15.x (latest available)
- **Templates**: Select "Free tier"

#### Settings
- **DB instance identifier**: `siteguard-db` (or your preferred name)
- **Master username**: `postgres` (default)
- **Master password**: Create a strong password (save this securely!)
- **Confirm password**: Re-enter the password

#### DB Instance Class
- **Instance class**: db.t3.micro (should be pre-selected with Free tier template)
- This provides: 2 vCPUs, 1 GB RAM

#### Storage
- **Storage type**: General Purpose SSD (gp2)
- **Allocated storage**: 20 GB (Free tier limit)
- **Storage autoscaling**: Disable (to stay within free tier)

#### Connectivity
- **Compute resource**: Don't connect to an EC2 compute resource
- **VPC**: Default VPC
- **Subnet group**: default
- **Public access**: Yes (required for development access)
- **VPC security group**: Create new
  - **New VPC security group name**: `siteguard-db-sg`
- **Availability Zone**: No preference

#### Database Authentication
- **Database authentication**: Password authentication

#### Additional Configuration (Expand this section)

**Database options:**
- **Initial database name**: `siteguard` (this creates the database automatically)
- **DB parameter group**: default.postgres15
- **Option group**: default:postgres-15

**Backup:**
- **Enable automated backups**: Yes (checked)
- **Backup retention period**: 7 days
- **Backup window**: No preference
- **Copy tags to snapshots**: Yes (checked)

**Encryption:**
- **Enable encryption**: Yes (recommended, still free tier)
- **AWS KMS key**: (default) aws/rds

**Monitoring:**
- **Enable Enhanced monitoring**: No (to stay in free tier)

**Maintenance:**
- **Enable auto minor version upgrade**: Yes (recommended)
- **Maintenance window**: No preference

**Deletion protection:**
- **Enable deletion protection**: No (for easy teardown after demo)

### Step 5: Create Database

1. Review all settings
2. Click "Create database" button
3. Wait 5-10 minutes for the database to be created
4. Status will change from "Creating" to "Available"

### Step 6: Configure Security Group

Once the database is created:

1. Click on your database instance name (`siteguard-db`)
2. Scroll to "Connectivity & security" section
3. Click on the VPC security group link (e.g., `siteguard-db-sg`)
4. Click "Edit inbound rules"
5. Click "Add rule"
   - **Type**: PostgreSQL
   - **Protocol**: TCP
   - **Port**: 5432
   - **Source**: My IP (or paste your IP from Step 1)
   - **Description**: Development access
6. Click "Save rules"

### Step 7: Get Connection Details

1. Go back to RDS console
2. Click on your database instance
3. In "Connectivity & security" section, find:
   - **Endpoint**: (e.g., `siteguard-db.xxxxx.us-east-1.rds.amazonaws.com`)
   - **Port**: 5432
4. Copy the endpoint URL

### Step 8: Update .env File

Add these variables to your `.env` file:

```bash
# AWS RDS PostgreSQL Configuration
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_ENDPOINT:5432/siteguard
DB_HOST=YOUR_ENDPOINT
DB_PORT=5432
DB_NAME=siteguard
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
```

Replace:
- `YOUR_PASSWORD` with the master password you created
- `YOUR_ENDPOINT` with the endpoint from Step 7

### Step 9: Test Connection

Run the validation script:
```bash
python scripts/validate_rds_connection.py
```

## Cost Monitoring

To ensure you stay within Free Tier:

1. Go to AWS Billing Dashboard
2. Set up a billing alert for $1
3. Monitor RDS usage:
   - 750 hours/month of db.t3.micro usage (Free Tier)
   - 20 GB of storage (Free Tier)
   - 20 GB of backup storage (Free Tier)

## Teardown Instructions

When you're done with the demo:

1. Go to RDS Console
2. Select your database instance
3. Click "Actions" → "Delete"
4. Uncheck "Create final snapshot"
5. Check "I acknowledge..."
6. Type "delete me" in the confirmation box
7. Click "Delete"

Or use the teardown script:
```bash
python scripts/teardown_aws.py
```

## Troubleshooting

### Cannot connect to database
- Verify security group allows your IP on port 5432
- Verify "Public access" is set to "Yes"
- Check your IP hasn't changed (dynamic IPs)
- Verify endpoint URL is correct

### Database creation failed
- Check you haven't exceeded Free Tier limits
- Verify you selected db.t3.micro instance type
- Check AWS service health status

### Connection timeout
- Security group may not be configured correctly
- Database may not be publicly accessible
- Check VPC and subnet configuration

## Additional Resources

- [AWS RDS Free Tier](https://aws.amazon.com/rds/free/)
- [PostgreSQL on RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)
- [RDS Security Groups](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html)
