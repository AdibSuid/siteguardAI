# Requirements Document: AWS Database & Authentication Integration

## Introduction

This specification defines the requirements for integrating AWS-managed database (RDS PostgreSQL) and authentication (Cognito) into the SiteGuard AI system to demonstrate enterprise-grade infrastructure capabilities for the CAIE project presentation.

**Scope**: Demo-ready implementation using AWS Free Tier services that can be easily deployed and torn down after presentation.

**Timeline**: 1-2 days implementation, 1-2 weeks demo period, then teardown.

**Cost Target**: $0-5 using AWS Free Tier.

## Glossary

- **System**: SiteGuard AI application (FastAPI backend + Streamlit frontend)
- **RDS**: AWS Relational Database Service (managed PostgreSQL)
- **Azure_AD_B2C**: Microsoft Azure Active Directory B2C for authentication and user management
- **SSO**: Single Sign-On authentication using Microsoft accounts
- **Free_Tier**: AWS free usage limits for new accounts (12 months)
- **User**: Person accessing the SiteGuard AI system
- **Report**: Generated safety incident report stored in database
- **Violation**: Detected PPE safety violation
- **Session**: Authenticated user session with JWT token
- **Admin**: User with elevated privileges for system management

## Requirements

### Requirement 1: AWS RDS PostgreSQL Database Integration

**User Story:** As a system administrator, I want all reports and violations stored in a managed PostgreSQL database, so that data persists reliably and can be queried for analytics.

#### Acceptance Criteria

1. WHEN the system starts, THE System SHALL connect to AWS RDS PostgreSQL instance
2. WHEN a report is generated, THE System SHALL store it in the database with all metadata
3. WHEN a violation is detected, THE System SHALL store it in the violations table with timestamp and location
4. WHEN a user requests report history, THE System SHALL retrieve reports from database ordered by timestamp
5. WHEN the database connection fails, THE System SHALL log the error and return a user-friendly message
6. THE Database SHALL use SQLAlchemy ORM for all database operations
7. THE Database SHALL include proper indexes on frequently queried fields (timestamp, location, violation_type)
8. WHEN the system initializes, THE System SHALL automatically create database tables if they don't exist

### Requirement 2: Microsoft Azure AD B2C Authentication (SSO)

**User Story:** As a safety officer, I want to log in with my Microsoft account, so that I can access the system securely using enterprise Single Sign-On.

#### Acceptance Criteria

1. WHEN a user visits the login page, THE System SHALL display a "Sign in with Microsoft" button
2. WHEN a user clicks the Microsoft sign-in button, THE System SHALL redirect to Microsoft Azure AD B2C login page
3. WHEN a user authenticates with valid Microsoft credentials, THE System SHALL receive an OAuth 2.0 authorization code
4. WHEN the authorization code is received, THE System SHALL exchange it for a JWT access token and ID token
5. WHEN a user enters invalid credentials, THE Microsoft login page SHALL display an error message and deny access
6. WHEN an authenticated user makes API requests, THE System SHALL validate the JWT token from Microsoft
7. WHEN a JWT token expires, THE System SHALL prompt the user to re-authenticate via Microsoft
8. THE System SHALL support Microsoft personal accounts (outlook.com, hotmail.com) and organizational accounts
9. WHEN a user logs out, THE System SHALL invalidate the session and clear tokens
10. THE System SHALL extract user information (email, name) from the Microsoft ID token

### Requirement 3: Role-Based Access Control (RBAC)

**User Story:** As a system administrator, I want different user roles with different permissions, so that I can control who can perform sensitive operations.

#### Acceptance Criteria

1. THE System SHALL support three user roles: Admin, Safety_Officer, and Viewer
2. WHEN an Admin user is authenticated, THE System SHALL allow full access to all features
3. WHEN a Safety_Officer user is authenticated, THE System SHALL allow report generation and viewing
4. WHEN a Viewer user is authenticated, THE System SHALL allow read-only access to reports
5. WHEN a user attempts an unauthorized action, THE System SHALL return a 403 Forbidden error
6. THE System SHALL store user roles in the database linked to Microsoft user ID
7. WHEN a user's role changes, THE System SHALL reflect the new permissions on next login
8. THE System SHALL assign default "Viewer" role to new users on first login

### Requirement 4: Database Schema Design

**User Story:** As a developer, I want a well-designed database schema, so that data is organized efficiently and queries perform well.

#### Acceptance Criteria

1. THE Database SHALL include a "reports" table with fields: id, report_id, title, text, location, timestamp, user_id, format, metadata_json
2. THE Database SHALL include a "violations" table with fields: id, violation_type, severity, description, osha_standard, confidence, timestamp, location, report_id
3. THE Database SHALL include a "users" table with fields: id, microsoft_user_id, email, name, role, created_at, last_login
4. THE Database SHALL include a "detection_history" table with fields: id, image_path, detection_count, violation_count, inference_time_ms, timestamp, user_id
5. THE Database SHALL use foreign keys to maintain referential integrity between tables
6. THE Database SHALL use UUID for primary keys where appropriate
7. THE Database SHALL include created_at and updated_at timestamps on all tables
8. THE users table SHALL store microsoft_user_id as unique identifier from Azure AD

### Requirement 5: API Authentication Middleware

**User Story:** As a developer, I want API endpoints protected by authentication, so that unauthorized users cannot access sensitive operations.

#### Acceptance Criteria

1. WHEN an API request is made to protected endpoints, THE System SHALL verify the JWT token in the Authorization header
2. WHEN a valid JWT token is provided, THE System SHALL extract user information and proceed with the request
3. WHEN an invalid or missing JWT token is provided, THE System SHALL return a 401 Unauthorized error
4. THE System SHALL implement a dependency function for FastAPI route protection
5. THE System SHALL support both API key authentication (for programmatic access) and JWT authentication (for users)
6. WHEN an API key is used, THE System SHALL validate it against stored API keys in the database

### Requirement 6: Streamlit Microsoft SSO Integration

**User Story:** As a user, I want to log in through the Streamlit interface using my Microsoft account, so that I can access the web dashboard securely with Single Sign-On.

#### Acceptance Criteria

1. WHEN a user visits the Streamlit app, THE System SHALL check for an active Microsoft session
2. WHEN no active session exists, THE System SHALL display a "Sign in with Microsoft" button
3. WHEN a user clicks the sign-in button, THE System SHALL redirect to Microsoft Azure AD B2C login
4. WHEN authentication succeeds, THE System SHALL store the JWT token in Streamlit session state
5. WHEN a user logs out, THE System SHALL clear the session state and redirect to login
6. THE System SHALL display the logged-in user's name and email in the sidebar
7. THE System SHALL show a logout button in the sidebar for authenticated users
8. WHEN the JWT token expires during a session, THE System SHALL prompt for re-authentication
9. THE System SHALL handle OAuth callback and token exchange within Streamlit

### Requirement 7: Azure Free Tier Compliance

**User Story:** As a student, I want to use Azure and AWS services within free tier limits, so that I can demonstrate enterprise features without incurring significant costs.

#### Acceptance Criteria

1. THE RDS instance SHALL use db.t3.micro or db.t4g.micro instance type (AWS free tier eligible)
2. THE RDS instance SHALL use 20GB or less of storage (AWS free tier limit)
3. THE System SHALL use Azure AD B2C free tier (up to 50,000 MAUs)
4. THE System SHALL monitor AWS and Azure usage to stay within free tier limits
5. THE System SHALL include documentation on how to tear down all AWS and Azure resources after demo
6. THE System SHALL use infrastructure-as-code for easy resource provisioning and teardown

### Requirement 8: Environment Configuration

**User Story:** As a developer, I want AWS credentials and configuration managed securely, so that sensitive information is not exposed in code.

#### Acceptance Criteria

1. THE System SHALL load AWS credentials from environment variables or AWS credentials file
2. THE System SHALL load database connection string from environment variables
3. THE System SHALL load Azure AD B2C configuration (Tenant ID, Client ID, Client Secret) from environment variables
4. THE System SHALL never commit AWS or Azure credentials to version control
5. THE System SHALL provide a .env.example file with all required AWS and Azure configuration variables
6. THE System SHALL validate all required environment variables on startup

### Requirement 9: Database Migration Management

**User Story:** As a developer, I want database schema changes managed through migrations, so that database updates are versioned and reproducible.

#### Acceptance Criteria

1. THE System SHALL use Alembic for database migrations
2. WHEN the database schema changes, THE System SHALL generate a new migration file
3. WHEN deploying, THE System SHALL automatically run pending migrations
4. THE System SHALL support rollback of migrations if needed
5. THE System SHALL version all migration files in source control

### Requirement 10: Analytics and Reporting Queries

**User Story:** As a safety manager, I want to query historical data for analytics, so that I can identify trends and improve safety protocols.

#### Acceptance Criteria

1. WHEN a user requests violation trends, THE System SHALL query the database and return aggregated data by date
2. WHEN a user requests compliance rate, THE System SHALL calculate the percentage of compliant vs. non-compliant detections
3. WHEN a user requests top violation types, THE System SHALL return the most common violations with counts
4. WHEN a user requests location-based analytics, THE System SHALL group violations by location
5. THE System SHALL cache frequently accessed analytics queries for performance
6. THE System SHALL support date range filtering for all analytics queries

### Requirement 11: Data Backup and Recovery

**User Story:** As a system administrator, I want automated database backups, so that data can be recovered in case of failure.

#### Acceptance Criteria

1. THE RDS instance SHALL have automated backups enabled with 7-day retention
2. THE System SHALL support manual database snapshots before major changes
3. THE System SHALL document the backup restoration procedure
4. WHEN a backup is restored, THE System SHALL verify data integrity

### Requirement 12: Performance and Optimization

**User Story:** As a user, I want fast database queries, so that the application remains responsive even with historical data.

#### Acceptance Criteria

1. WHEN querying reports, THE System SHALL return results in under 500ms for up to 10,000 records
2. THE Database SHALL use connection pooling to manage database connections efficiently
3. THE System SHALL implement pagination for large result sets (max 100 records per page)
4. THE System SHALL use database indexes on frequently queried columns
5. WHEN the database connection pool is exhausted, THE System SHALL queue requests and return appropriate error messages

### Requirement 13: Monitoring and Logging

**User Story:** As a system administrator, I want to monitor database and authentication activity, so that I can troubleshoot issues and detect anomalies.

#### Acceptance Criteria

1. THE System SHALL log all database connection attempts (success and failure)
2. THE System SHALL log all authentication attempts (success and failure)
3. THE System SHALL log slow database queries (>1 second)
4. THE System SHALL track authentication metrics (login count, failed attempts, active sessions)
5. THE System SHALL provide a health check endpoint that verifies database connectivity

### Requirement 14: Teardown and Cleanup

**User Story:** As a student, I want to easily remove all AWS resources after the demo, so that I don't incur ongoing charges.

#### Acceptance Criteria

1. THE System SHALL provide a teardown script that deletes all AWS resources
2. THE Teardown script SHALL delete the RDS instance
3. THE Teardown script SHALL delete the Azure AD B2C tenant (or document manual deletion)
4. THE Teardown script SHALL delete any S3 buckets created for the project
5. THE Teardown script SHALL confirm deletion before proceeding
6. THE System SHALL document the manual steps to verify all resources are deleted

### Requirement 15: Demo Data Seeding

**User Story:** As a presenter, I want sample data in the database for demonstration, so that I can showcase analytics and reporting features.

#### Acceptance Criteria

1. THE System SHALL provide a data seeding script that creates sample users
2. THE Seeding script SHALL create sample reports with various violation types
3. THE Seeding script SHALL create sample violations across different locations and dates
4. THE Seeding script SHALL create realistic detection history data
5. THE Seeded data SHALL demonstrate trends and patterns for analytics showcase
6. THE System SHALL support clearing seeded data and starting fresh

### Requirement 16: Microsoft Identity Integration

**User Story:** As a system administrator, I want to leverage Microsoft identity features, so that the system integrates seamlessly with enterprise Microsoft environments.

#### Acceptance Criteria

1. WHEN a user logs in with Microsoft, THE System SHALL retrieve user profile information (name, email, photo)
2. THE System SHALL display the user's Microsoft profile picture in the Streamlit sidebar
3. THE System SHALL support both Microsoft personal accounts and organizational accounts (Azure AD)
4. WHEN a user from an organization logs in, THE System SHALL display their organization name
5. THE System SHALL handle Microsoft token refresh automatically when tokens expire
6. THE System SHALL support Microsoft multi-factor authentication (MFA) if enabled on the account
7. THE System SHALL log Microsoft authentication events for audit purposes

---

## Non-Functional Requirements

### Performance
- Database queries SHALL complete in under 500ms for typical operations
- Authentication SHALL complete in under 2 seconds
- System SHALL support at least 50 concurrent users

### Security
- All database connections SHALL use SSL/TLS encryption
- JWT tokens SHALL expire after 1 hour
- Passwords SHALL never be stored in plain text (handled by Cognito)
- API keys SHALL be hashed before storage

### Reliability
- System SHALL have 99% uptime during demo period
- Database SHALL have automated backups
- System SHALL gracefully handle AWS service outages

### Usability
- Login process SHALL require no more than 3 clicks
- Error messages SHALL be clear and actionable
- System SHALL provide visual feedback for all operations

### Maintainability
- All AWS resources SHALL be defined in infrastructure-as-code
- Database schema SHALL be version controlled
- Configuration SHALL be externalized from code

---

## Success Criteria

The implementation is successful when:

1. ✅ All reports and violations are stored in AWS RDS PostgreSQL
2. ✅ Users can login using Microsoft accounts (SSO)
3. ✅ API endpoints are protected with JWT authentication from Microsoft
4. ✅ Streamlit dashboard requires Microsoft authentication
5. ✅ Role-based access control is enforced
6. ✅ Analytics queries return historical data from database
7. ✅ System stays within AWS and Azure Free Tier limits
8. ✅ All AWS and Azure resources can be torn down in under 10 minutes
9. ✅ Demo data is seeded and showcases system capabilities
10. ✅ Audience sees "Sign in with Microsoft" button and enterprise-grade infrastructure

---

## Out of Scope

The following are explicitly NOT included in this implementation:

- ❌ Multi-region deployment
- ❌ Advanced AWS services (Lambda, Step Functions, etc.)
- ❌ Production-grade high availability setup
- ❌ Advanced monitoring (CloudWatch dashboards)
- ❌ Cost optimization beyond free tier
- ❌ Data encryption at rest (beyond RDS defaults)
- ❌ Advanced security features (WAF, Shield)
- ❌ Integration with existing enterprise systems

---

## Dependencies

- AWS Account with Free Tier eligibility
- Python 3.10+
- SQLAlchemy 2.0+
- Alembic for migrations
- boto3 for AWS SDK
- msal (Microsoft Authentication Library) for Azure AD B2C
- python-jose for JWT handling
- psycopg2 for PostgreSQL driver
- requests-oauthlib for OAuth 2.0 flow

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWS Free Tier exceeded | Cost overrun | Monitor usage, set billing alerts, teardown after demo |
| Database connection issues | System unavailable | Implement retry logic, connection pooling |
| Authentication complexity | Development delay | Use AWS Amplify libraries, follow AWS documentation |
| Data loss during demo | Poor presentation | Enable automated backups, test restore procedure |
| Slow database queries | Poor user experience | Use indexes, implement caching, optimize queries |

---

**Document Version:** 1.0  
**Created:** January 2026  
**Status:** Ready for Design Phase
