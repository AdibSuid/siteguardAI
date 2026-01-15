# Fix MySQL Authentication Error

## Problem

```
Access denied for user 'siteguard'@'42.190.91.98' (using password: YES)
```

This means either:
1. The username is wrong
2. The password is wrong
3. The user doesn't exist in the database

## Solution

### Option 1: Find the Correct Master Username

The master username was set when you created the RDS instance.

**Check in AWS Console:**
1. Go to AWS RDS Console: https://console.aws.amazon.com/rds/
2. Click on your database: **siteguard-db**
3. Look in the "Configuration" tab
4. Find "Master username" - this is the correct username

**Common master usernames:**
- `admin` (default for MySQL/Aurora)
- `root`
- `siteguard`
- Whatever you typed during creation

### Option 2: Reset the Master Password

If you forgot the password or it's not working:

1. Go to AWS RDS Console
2. Click on your database: **siteguard-db**
3. Click "Modify" button
4. Scroll to "Settings" section
5. Check "New master password"
6. Enter a new password (save it securely!)
7. Confirm the password
8. Click "Continue"
9. Select "Apply immediately"
10. Click "Modify DB instance"
11. Wait 2-3 minutes for the change to apply

### Option 3: Check Password Special Characters

Your password has a `#` character: `AhmadSpiderman67#`

In the DATABASE_URL, special characters must be URL-encoded:
- `#` becomes `%23`
- `@` becomes `%40`
- `&` becomes `%26`
- `=` becomes `%3D`
- `+` becomes `%2B`

**Your current .env has:**
```bash
DATABASE_URL=mysql+pymysql://siteguard:AhmadSpiderman67%23@...
```

This looks correct (# is encoded as %23).

But the individual password field has:
```bash
DB_PASSWORD=AhmadSpiderman67#
```

This is also correct for the individual field.

## Steps to Fix

### Step 1: Verify Master Username

Check AWS Console for the actual master username.

If it's **NOT** `siteguard`, update your .env:

```bash
# If master username is 'admin'
DATABASE_URL=mysql+pymysql://admin:AhmadSpiderman67%23@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_USER=admin

# If master username is 'root'
DATABASE_URL=mysql+pymysql://root:AhmadSpiderman67%23@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_USER=root
```

### Step 2: Verify Password

If the username is correct but password is wrong:

1. Reset password in AWS Console (see Option 2 above)
2. Update .env with new password
3. Remember to URL-encode special characters in DATABASE_URL

### Step 3: Test Connection

```bash
python scripts/validate_mysql_connection.py
```

## Common Scenarios

### Scenario 1: Master username is 'admin'

Update .env:
```bash
DATABASE_URL=mysql+pymysql://admin:AhmadSpiderman67%23@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_USER=admin
DB_PASSWORD=AhmadSpiderman67#
```

### Scenario 2: Password was different

If you used a different password during RDS creation:

1. Check your notes/password manager
2. Or reset the password in AWS Console
3. Update .env with correct password

### Scenario 3: Need to create 'siteguard' user

If the master username is different (e.g., 'admin'), you can:

1. First connect with master username
2. Create the 'siteguard' user
3. Grant permissions
4. Then use 'siteguard' user

But for now, **just use the master username** to get connected.

## Quick Test

Try connecting with different username:

```bash
# Test with 'admin' username
python -c "import pymysql; conn = pymysql.connect(host='siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com', port=3306, user='admin', password='AhmadSpiderman67#', database='siteguard-db'); print('✓ Connected with admin'); conn.close()"

# Test with 'root' username
python -c "import pymysql; conn = pymysql.connect(host='siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com', port=3306, user='root', password='AhmadSpiderman67#', database='siteguard-db'); print('✓ Connected with root'); conn.close()"

# Test with 'siteguard' username
python -c "import pymysql; conn = pymysql.connect(host='siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com', port=3306, user='siteguard', password='AhmadSpiderman67#', database='siteguard-db'); print('✓ Connected with siteguard'); conn.close()"
```

Whichever one works, use that username in your .env file.

## After Fixing

Once you have the correct username and password:

1. Update .env file
2. Run: `python scripts/validate_mysql_connection.py`
3. Should see: `✓ All validation tests passed!`
4. Mark Task 2 as complete

## Need Help?

Check these in AWS Console:
1. Database name: Configuration tab → "DB name"
2. Master username: Configuration tab → "Master username"
3. Endpoint: Connectivity & security tab → "Endpoint"
4. Port: Connectivity & security tab → "Port"
