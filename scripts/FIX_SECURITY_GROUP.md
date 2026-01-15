# Fix Security Group for MySQL RDS Connection

## Problem

Connection timeout error:
```
Can't connect to MySQL server on 'siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com' (timed out)
```

This means your security group is **NOT allowing connections** from your IP address.

## Solution: Configure Security Group

### Step 1: Find Your Current IP

Your IP address: **42.190.91.98**

(Run `python scripts/get_public_ip.py` if it changed)

### Step 2: Go to AWS RDS Console

1. Open https://console.aws.amazon.com/rds/
2. Click on "Databases" in the left sidebar
3. Click on your database: **siteguard-db**

### Step 3: Find the Security Group

1. Scroll to the "Connectivity & security" tab
2. Look for "VPC security groups"
3. You should see a security group link (e.g., `sg-xxxxxxxxx`)
4. **Click on the security group link**

### Step 4: Edit Inbound Rules

1. You'll be taken to the EC2 Security Groups page
2. Click on the "Inbound rules" tab
3. Click "Edit inbound rules" button

### Step 5: Add MySQL Rule

Click "Add rule" and configure:

```
Type:        MYSQL/Aurora
Protocol:    TCP
Port range:  3306
Source:      Custom
CIDR:        42.190.91.98/32
Description: Development access from my IP
```

**IMPORTANT:** 
- Type must be "MYSQL/Aurora" (NOT PostgreSQL)
- Port must be 3306 (NOT 5432)
- Source must be your IP: 42.190.91.98/32

### Step 6: Save Rules

1. Click "Save rules" button
2. Wait 10-30 seconds for changes to take effect

### Step 7: Verify Public Access

Back in RDS Console:

1. Click on your database: **siteguard-db**
2. Scroll to "Connectivity & security"
3. Check "Publicly accessible": Should be **Yes**

If it says "No":
1. Click "Modify" button
2. Scroll to "Connectivity"
3. Change "Public access" to **Yes**
4. Click "Continue"
5. Select "Apply immediately"
6. Click "Modify DB instance"

### Step 8: Test Connection

```bash
python scripts/validate_mysql_connection.py
```

Expected output:
```
✓ Successfully connected to database
✓ MySQL version: 8.0.x
✓ Connected to database: siteguard-db
```

## Visual Guide

### What the Security Group Should Look Like

```
Inbound rules:
┌──────────────┬──────────┬──────────┬─────────────────┬─────────────────┐
│ Type         │ Protocol │ Port     │ Source          │ Description     │
├──────────────┼──────────┼──────────┼─────────────────┼─────────────────┤
│ MYSQL/Aurora │ TCP      │ 3306     │ 42.190.91.98/32 │ Dev access      │
└──────────────┴──────────┴──────────┴─────────────────┴─────────────────┘
```

## Common Mistakes

### ❌ Wrong Port
- Using port 5432 (PostgreSQL) instead of 3306 (MySQL)
- **Fix:** Change to port 3306

### ❌ Wrong Type
- Selecting "PostgreSQL" instead of "MYSQL/Aurora"
- **Fix:** Select "MYSQL/Aurora" from dropdown

### ❌ Wrong Source
- Using 0.0.0.0/0 (allows all IPs - insecure)
- Using wrong IP address
- **Fix:** Use your specific IP: 42.190.91.98/32

### ❌ Public Access Disabled
- RDS instance not publicly accessible
- **Fix:** Modify instance to enable public access

## Troubleshooting

### Still timing out after adding rule?

1. **Wait 30 seconds** - Security group changes take time
2. **Check your IP** - Run `python scripts/get_public_ip.py`
3. **Verify rule was saved** - Go back to security group and check
4. **Check RDS status** - Must be "Available" not "Modifying"

### IP keeps changing?

If you have a dynamic IP:
1. Update security group each time IP changes
2. Or use a broader CIDR range (less secure)
3. Or use a VPN with static IP

### Can't find security group?

1. Go to RDS Console
2. Click your database
3. Look under "Connectivity & security"
4. The security group is listed there

## After Fixing

Once the security group is configured:

```bash
# Test connection
python scripts/validate_mysql_connection.py

# Should see:
✓ All validation tests passed!
```

Then you can proceed with:
1. ✓ Mark Task 2 as complete
2. → Task 3: Implement database models (adapted for MySQL)
3. → Task 4: Set up Alembic migrations

## Need Help?

If you're still having issues:
1. Screenshot your security group inbound rules
2. Screenshot your RDS connectivity settings
3. Verify your IP with: `python scripts/get_public_ip.py`
4. Check RDS instance status is "Available"
