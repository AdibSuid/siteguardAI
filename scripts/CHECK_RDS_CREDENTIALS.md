# Check RDS Credentials in AWS Console

## Problem

All common usernames failed authentication, which means either:
1. The password is incorrect
2. The master username is non-standard

## Solution: Check AWS Console

### Step 1: Find Master Username

1. Go to **AWS RDS Console**: https://console.aws.amazon.com/rds/
2. Click on **Databases** in the left sidebar
3. Click on your database: **siteguard-db**
4. Click on the **Configuration** tab
5. Look for **"Master username"**
6. **Write it down**: `_______________________`

### Step 2: Verify Database Name

While you're there, also check:
- **DB name**: Should be `siteguard-db` (or note what it actually is)
- **Endpoint**: Should match what's in your .env
- **Port**: Should be 3306

### Step 3: Reset Master Password (Recommended)

Since the password isn't working, let's reset it:

1. Still in RDS Console, click your database: **siteguard-db**
2. Click the **"Modify"** button (top right)
3. Scroll down to **"Settings"** section
4. Check the box: **"New master password"**
5. Enter a new password: `_______________________`
   - Use a strong password
   - Avoid special characters for simplicity (or remember to URL-encode them)
   - Example: `SiteGuard2026Secure` (no special chars)
6. Confirm the password
7. Scroll to bottom, click **"Continue"**
8. Select **"Apply immediately"**
9. Click **"Modify DB instance"**
10. **Wait 2-3 minutes** for the change to apply

### Step 4: Update .env File

Once you have the correct username and new password, update your .env:

```bash
# Example if master username is 'admin' and new password is 'SiteGuard2026Secure'
DATABASE_URL=mysql+pymysql://admin:SiteGuard2026Secure@siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com:3306/siteguard-db
DB_HOST=siteguard-db.cela8keww4th.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_NAME=siteguard-db
DB_USER=admin
DB_PASSWORD=SiteGuard2026Secure
```

**Important:** If your password has special characters, URL-encode them in DATABASE_URL:
- `#` → `%23`
- `@` → `%40`
- `&` → `%26`
- `=` → `%3D`
- `+` → `%2B`
- `space` → `%20`

### Step 5: Test Connection

```bash
python scripts/validate_mysql_connection.py
```

Expected output:
```
✓ Successfully connected to database
✓ MySQL version: 8.0.x
✓ All validation tests passed!
```

## Quick Reference

### What to Check in AWS Console

| Setting | Where to Find | What to Look For |
|---------|---------------|------------------|
| Master username | Configuration tab | Usually 'admin', 'root', or custom |
| Database name | Configuration tab | Should be 'siteguard-db' |
| Endpoint | Connectivity & security | Should match .env |
| Port | Connectivity & security | Should be 3306 |
| Status | Summary | Should be "Available" |

### Common Master Usernames

- `admin` - Default for Aurora/RDS MySQL
- `root` - Traditional MySQL default
- Custom name you entered during creation

### Password Reset Time

- Modification takes 2-3 minutes
- Status will show "Modifying" then "Available"
- Don't try to connect while status is "Modifying"

## Troubleshooting

### Can't find Configuration tab
- Make sure you clicked on the database name (not checkbox)
- Should see tabs: Connectivity & security, Monitoring, Logs & events, Configuration, etc.

### Modify button is grayed out
- Database might be in "Modifying" state
- Wait for it to become "Available"
- Refresh the page

### Password reset not working
- Make sure you selected "Apply immediately"
- Wait full 2-3 minutes
- Check database status is "Available" before testing

### Still can't connect after reset
- Double-check you updated .env with new password
- Verify no typos in username or password
- Check special characters are URL-encoded in DATABASE_URL
- Verify security group still allows your IP

## After Successful Connection

Once validation passes:
1. ✓ Mark Task 2 as complete
2. → Proceed to Task 3: Implement database models
3. → Continue with remaining tasks

## Need More Help?

If you're still stuck:
1. Take a screenshot of the Configuration tab
2. Take a screenshot of the Connectivity & security tab
3. Verify the exact error message
4. Check AWS RDS service health status
