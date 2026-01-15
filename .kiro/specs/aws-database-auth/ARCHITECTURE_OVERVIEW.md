# SiteGuard AI - Enterprise Architecture with Microsoft SSO

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Streamlit Web   │         │   FastAPI REST   │         │
│  │    Dashboard     │◄────────┤      API         │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                            │                    │
└───────────┼────────────────────────────┼────────────────────┘
            │                            │
            │  ┌─────────────────────────┼──────────┐
            │  │                         │          │
            ▼  ▼                         ▼          ▼
┌───────────────────┐         ┌──────────────────────────┐
│  MICROSOFT AZURE  │         │      AWS SERVICES        │
├───────────────────┤         ├──────────────────────────┤
│                   │         │                          │
│  Azure AD B2C     │         │  RDS PostgreSQL          │
│  ┌─────────────┐ │         │  ┌────────────────────┐  │
│  │ OAuth 2.0   │ │         │  │  Reports Table     │  │
│  │ JWT Tokens  │ │         │  │  Violations Table  │  │
│  │ User Mgmt   │ │         │  │  Users Table       │  │
│  └─────────────┘ │         │  │  Detection History │  │
│                   │         │  └────────────────────┘  │
│  "Sign in with    │         │                          │
│   Microsoft"      │         │  db.t3.micro (Free Tier) │
└───────────────────┘         └──────────────────────────┘
            │                            │
            └────────────┬───────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   APPLICATION LAYER    │
            ├────────────────────────┤
            │  • PPE Detection       │
            │  • Report Generation   │
            │  • Analytics Engine    │
            │  • Role-Based Access   │
            └────────────────────────┘
```

## 🔐 Authentication Flow

```
┌──────┐                                    ┌──────────────┐
│ User │                                    │  Streamlit   │
└───┬──┘                                    │     App      │
    │                                       └──────┬───────┘
    │ 1. Visit App                                 │
    ├─────────────────────────────────────────────►
    │                                              │
    │ 2. Show "Sign in with Microsoft"            │
    │◄─────────────────────────────────────────────┤
    │                                              │
    │ 3. Click Sign In                             │
    ├─────────────────────────────────────────────►
    │                                              │
    │                                              │ 4. Redirect to Azure AD
    │                                              ├──────────────┐
    │                                              │              │
    │                                              │              ▼
    │                                              │    ┌──────────────────┐
    │ 5. Microsoft Login Page                     │    │   Azure AD B2C   │
    │◄─────────────────────────────────────────────────┤  Login Page      │
    │                                              │    └──────────────────┘
    │ 6. Enter Microsoft Credentials               │              │
    ├──────────────────────────────────────────────────────────────►
    │                                              │              │
    │ 7. Authorization Code                        │              │
    │◄─────────────────────────────────────────────────────────────┤
    │                                              │              │
    │                                              │ 8. Exchange for JWT
    │                                              ├──────────────►
    │                                              │              │
    │                                              │ 9. JWT Token │
    │                                              │◄──────────────┤
    │                                              │              │
    │ 10. Authenticated Session                    │              │
    │◄─────────────────────────────────────────────┤              │
    │                                              │              │
    │ 11. Access Protected Features                │              │
    ├─────────────────────────────────────────────►              │
    │                                              │              │
```

## 📊 Database Schema

```sql
-- Users Table (linked to Microsoft accounts)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    microsoft_user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'Viewer',
    profile_picture_url TEXT,
    organization VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_microsoft_user_id (microsoft_user_id),
    INDEX idx_email (email)
);

-- Reports Table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    text TEXT NOT NULL,
    location VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    user_id UUID REFERENCES users(id),
    format VARCHAR(50),
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_location (location),
    INDEX idx_user_id (user_id)
);

-- Violations Table
CREATE TABLE violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    violation_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    description TEXT,
    osha_standard VARCHAR(50),
    confidence DECIMAL(5,4),
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(255) NOT NULL,
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_violation_type (violation_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_location (location),
    INDEX idx_report_id (report_id)
);

-- Detection History Table
CREATE TABLE detection_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    image_path VARCHAR(500),
    detection_count INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    inference_time_ms DECIMAL(10,2),
    timestamp TIMESTAMP NOT NULL,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
);
```

## 🔑 Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# RDS PostgreSQL
DATABASE_URL=postgresql://username:password@your-rds-endpoint:5432/siteguard

# Microsoft Azure AD B2C
AZURE_AD_TENANT_ID=your_tenant_id
AZURE_AD_CLIENT_ID=your_client_id
AZURE_AD_CLIENT_SECRET=your_client_secret
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/your_tenant_id
AZURE_AD_REDIRECT_URI=http://localhost:8501/callback

# Application
SECRET_KEY=your_secret_key_for_sessions
ENVIRONMENT=development
```

## 💰 Cost Breakdown

### AWS Services (Free Tier - 12 months)
- **RDS PostgreSQL db.t3.micro**: 750 hours/month = **$0**
- **RDS Storage**: 20GB = **$0**
- **RDS Backup**: 20GB = **$0**
- **Data Transfer**: 15GB out = **$0**

### Azure Services (Free Tier - Always Free)
- **Azure AD B2C**: 50,000 MAUs = **$0**
- **Authentication Requests**: Unlimited = **$0**

### **Total Monthly Cost: $0** (within free tiers)

### After Free Tier Expires (AWS only)
- **RDS db.t3.micro**: ~$15/month
- **RDS Storage 20GB**: ~$2/month
- **Total**: ~$17/month

**Azure AD B2C remains free forever for <50,000 users**

## 🚀 Deployment Steps

### Day 1: AWS + Database (4-6 hours)

#### Step 1: AWS RDS Setup (1 hour)
```bash
# 1. Login to AWS Console
# 2. Navigate to RDS
# 3. Create PostgreSQL Database
#    - Engine: PostgreSQL 15
#    - Template: Free tier
#    - Instance: db.t3.micro
#    - Storage: 20GB
#    - Public access: Yes (for demo)
#    - Security group: Allow port 5432 from your IP

# 4. Wait for database to be available (~10 minutes)
# 5. Note the endpoint URL
```

#### Step 2: Database Connection (1 hour)
```bash
# Install dependencies
pip install sqlalchemy psycopg2-binary alembic

# Test connection
python scripts/test_db_connection.py

# Create tables
alembic upgrade head
```

#### Step 3: Integrate with Application (2 hours)
```python
# Add database models
# Update API endpoints to use database
# Test CRUD operations
```

#### Step 4: Seed Demo Data (1 hour)
```bash
python scripts/seed_demo_data.py
```

### Day 2: Microsoft SSO + Testing (4-6 hours)

#### Step 1: Azure AD B2C Setup (1.5 hours)
```bash
# 1. Login to Azure Portal
# 2. Create Azure AD B2C Tenant
# 3. Register Application
#    - Name: SiteGuard AI
#    - Redirect URI: http://localhost:8501/callback
#    - Platform: Web
# 4. Create Client Secret
# 5. Configure User Flows (Sign up and sign in)
# 6. Note: Tenant ID, Client ID, Client Secret
```

#### Step 2: Implement OAuth Flow (2 hours)
```bash
# Install dependencies
pip install msal requests-oauthlib

# Implement authentication
# - OAuth redirect
# - Token exchange
# - JWT validation
```

#### Step 3: Integrate with Streamlit (1.5 hours)
```python
# Add login button
# Handle OAuth callback
# Store session
# Protect routes
```

#### Step 4: Testing (1 hour)
```bash
# Test login flow
# Test role-based access
# Test database operations
# Test logout
```

## 🎬 Demo Script

### Opening (30 seconds)
> "SiteGuard AI uses enterprise-grade infrastructure. Let me show you the authentication system."

### Microsoft SSO Demo (1 minute)
1. Click "Sign in with Microsoft"
2. Show Microsoft login page
3. Enter credentials
4. Show successful login with profile picture
5. Point out: "This is the same authentication system used by Fortune 500 companies"

### Database Demo (1 minute)
1. Generate a report
2. Show it saved to database
3. Open AWS Console (optional)
4. Show RDS instance running
5. Point out: "All data persists in AWS RDS PostgreSQL, with automatic backups"

### Analytics Demo (1 minute)
1. Show analytics dashboard
2. Point out: "This data is queried from the database in real-time"
3. Show historical trends
4. Demonstrate role-based access

### Architecture Slide (30 seconds)
> "The system uses Microsoft Azure AD B2C for authentication and AWS RDS for data persistence. This architecture is production-ready and can scale to thousands of users."

## 🧹 Teardown Checklist

After your demo, follow these steps to avoid charges:

### AWS Cleanup (5 minutes)
```bash
# 1. Delete RDS Instance
aws rds delete-db-instance \
  --db-instance-identifier siteguard-db \
  --skip-final-snapshot

# 2. Delete Security Groups
aws ec2 delete-security-group --group-id sg-xxxxx

# 3. Verify deletion in AWS Console
```

### Azure Cleanup (5 minutes)
```bash
# 1. Delete App Registration
# 2. Delete Azure AD B2C Tenant (optional - it's free)
# 3. Verify no active resources
```

### Verification
```bash
# Check AWS billing dashboard
# Should show $0 charges

# Check Azure billing
# Should show $0 charges
```

## 📈 Success Metrics

Your implementation is successful when:

- ✅ Users can sign in with Microsoft accounts
- ✅ "Sign in with Microsoft" button appears on login
- ✅ User profile picture displays in sidebar
- ✅ All reports save to AWS RDS
- ✅ Analytics queries return data from database
- ✅ Role-based access control works
- ✅ System stays within free tier limits
- ✅ Audience is impressed by enterprise features
- ✅ Total cost is $0-5 for demo period

---

**Ready to implement!** 🚀

This architecture demonstrates:
- ✅ Enterprise authentication (Microsoft SSO)
- ✅ Cloud database (AWS RDS)
- ✅ Scalable infrastructure
- ✅ Security best practices
- ✅ Production-ready design

**All within free tier limits!**
