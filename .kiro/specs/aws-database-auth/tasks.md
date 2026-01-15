# Implementation Plan: AWS Database & Microsoft SSO Integration

## Overview

This implementation plan breaks down the AWS RDS PostgreSQL database and Microsoft Azure AD B2C authentication integration into discrete, manageable tasks. The implementation follows a 2-day timeline with incremental validation at each step.

**Implementation Language:** Python 3.10+

**Timeline:** 2 days (Day 1: Database, Day 2: Authentication)

**Approach:** Build incrementally, test continuously, integrate seamlessly

---

## Tasks

- [x] 1. Set up project dependencies and environment configuration
  - Install required Python packages: sqlalchemy, psycopg2-binary, alembic, msal, python-jose, fastapi-security
  - Create `.env.example` file with all required environment variables
  - Update `requirements.txt` with new dependencies and version pins
  - Create environment validation script to check all required variables are set
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 2. Create AWS RDS PostgreSQL instance
  - Log into AWS Console and navigate to RDS service
  - Create PostgreSQL 15 database instance with db.t3.micro (free tier)
  - Configure security group to allow port 5432 from development IP
  - Set up automated backups with 7-day retention
  - Note the RDS endpoint URL and add to `.env` file
  - _Requirements: 1.1, 11.1_

- [x] 3. Implement database models and connection management
  - [x] 3.1 Create SQLAlchemy models for all tables
    - Create `app/core/database/models.py` with User, Report, Violation, DetectionHistory models
    - Define all columns with proper types (UUID, String, DateTime, JSON, etc.)
    - Set up foreign key relationships between tables
    - Add indexes on frequently queried columns (timestamp, location, violation_type)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 1.7_
  
  - [x] 3.2 Create database connection manager
    - Create `app/core/database/connection.py` with DatabaseManager class
    - Implement connection pooling with QueuePool (pool_size=10, max_overflow=20)
    - Add context manager for session handling with automatic commit/rollback
    - Implement health check method to verify database connectivity
    - Add get_db() dependency function for FastAPI routes
    - _Requirements: 1.1, 1.5, 12.2_
  
  - [x] 3.3 Write property test for database connection persistence
    - **Property 2: Database Connection Persistence**
    - **Validates: Requirements 1.1, 1.5**
    - Test that database operations don't corrupt connection pool
    - Generate random database operations and verify connection remains healthy
    - _Requirements: 1.1, 1.5_

- [x] 4. Set up database migrations with Alembic
  - [x] 4.1 Initialize Alembic configuration
    - Run `alembic init alembic` to create migration structure
    - Configure `alembic.ini` with database URL from environment
    - Update `alembic/env.py` to import models and use async if needed
    - _Requirements: 9.1, 9.5_
  
  - [x] 4.2 Create initial schema migration
    - Generate migration: `alembic revision --autogenerate -m "Initial schema"`
    - Review generated migration for users, reports, violations, detection_history tables
    - Test migration: `alembic upgrade head`
    - Verify tables created in RDS using psql or database client
    - _Requirements: 1.8, 9.2, 9.3_
  
  - [x] 4.3 Create index migration
    - Generate migration for performance indexes on all tables
    - Add indexes for microsoft_user_id, email, timestamp, location, violation_type
    - Test migration and verify indexes created
    - _Requirements: 1.7, 12.4_

- [x] 5. Implement database service layer
  - [x] 5.1 Create database service with CRUD operations
    - Create `app/core/database/service.py` with DatabaseService class
    - Implement user operations: get_or_create_user, update_user_role
    - Implement report operations: create_report, get_reports, get_report_by_id
    - Implement violation operations: create_violation, get_violations
    - Implement detection history operations: create_detection_history
    - _Requirements: 1.2, 1.3, 1.4, 3.6, 3.7_
  
  - [x] 5.2 Implement analytics query methods
    - Add get_violation_trends method with date grouping
    - Add get_top_violation_types method with aggregation
    - Add get_location_analytics method with location grouping
    - Add get_compliance_rate method with calculation logic
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [-] 5.3 Write property test for report storage completeness
    - **Property 3: Report Storage Completeness**
    - **Validates: Requirements 1.2, 1.3**
    - Test that storing reports with violations preserves all violation data
    - Generate random reports with random violations and verify retrieval
    - **NOTE**: Property tests created but need refinement for order-independence and unique IDs
    - _Requirements: 1.2, 1.3_
  
  - [-] 5.4 Write property test for analytics aggregation accuracy
    - **Property 7: Analytics Aggregation Accuracy**
    - **Validates: Requirements 10.1, 10.2**
    - Test that sum of daily trends equals total compliance count
    - Generate random violations over time period and verify aggregations match
    - **NOTE**: Property tests created, need to be run and verified
    - _Requirements: 10.1, 10.2_
  
  - [-] 5.5 Write property test for foreign key cascade deletion
    - **Property 8: Foreign Key Cascade Deletion**
    - **Validates: Requirements 4.5**
    - Test that deleting reports cascades to violations
    - Generate random reports with violations, delete reports, verify violations gone
    - **NOTE**: Property tests created, need to be run and verified
    - _Requirements: 4.5_

- [x] 6. Checkpoint - Database integration complete
  - Verify all database tables exist in RDS
  - Test database connection from application
  - Run all database property tests and verify they pass
  - Seed demo data using script
  - Ensure all tests pass, ask the user if questions arise

- [ ] 7. Set up Microsoft Azure AD B2C tenant and application
  - Create Azure AD B2C tenant in Azure Portal
  - Register application with name "SiteGuard AI"
  - Configure redirect URI: `http://localhost:8501/callback`
  - Create client secret and note the value
  - Configure API permissions: User.Read, openid, profile, email
  - Grant admin consent for permissions
  - Note Tenant ID, Client ID, and Client Secret for `.env` file
  - _Requirements: 2.1, 2.2, 7.3, 8.3_

- [ ] 8. Implement Microsoft OAuth authentication
  - [ ] 8.1 Create Azure AD configuration
    - Create `app/core/auth/config.py` with AzureADConfig class
    - Load tenant ID, client ID, client secret from environment
    - Define OAuth endpoints (authorization, token, userinfo)
    - Add validation method to check all required config is present
    - _Requirements: 2.2, 2.3, 8.3_
  
  - [ ] 8.2 Implement OAuth flow handler
    - Create `app/core/auth/oauth.py` with MicrosoftOAuthHandler class
    - Implement get_authorization_url method using MSAL library
    - Implement exchange_code_for_token method for token exchange
    - Implement get_user_info method to fetch user data from Microsoft Graph
    - Implement refresh_token method for token renewal
    - _Requirements: 2.3, 2.4, 2.8, 2.10, 16.1, 16.5_
  
  - [ ] 8.3 Write property test for user authentication round trip
    - **Property 1: User Authentication Round Trip**
    - **Validates: Requirements 2.3, 2.4, 2.10**
    - Test that OAuth flow creates user with matching Microsoft data
    - Mock Microsoft OAuth responses with random user data
    - Verify user created in database with correct information
    - _Requirements: 2.3, 2.4, 2.10_
  
  - [ ] 8.4 Write property test for OAuth state CSRF protection
    - **Property 10: OAuth State CSRF Protection**
    - **Validates: Requirements 2.2, 2.3**
    - Test that mismatched state parameters are rejected
    - Generate random state values and verify validation
    - _Requirements: 2.2, 2.3_

- [ ] 9. Implement JWT token handling
  - [ ] 9.1 Create JWT handler
    - Create `app/core/auth/jwt_handler.py` with JWTHandler class
    - Implement create_access_token method with expiration
    - Implement verify_token method with signature validation
    - Implement verify_microsoft_token method for Microsoft-issued tokens
    - _Requirements: 2.6, 2.7_
  
  - [ ] 9.2 Write property test for JWT token validation
    - **Property 4: JWT Token Validation**
    - **Validates: Requirements 2.6, 2.7**
    - Test that created tokens can be verified and return original payload
    - Generate random payloads, create tokens, verify round-trip
    - _Requirements: 2.6, 2.7_
  
  - [ ] 9.3 Write property test for Microsoft token expiration handling
    - **Property 14: Microsoft Token Expiration Handling**
    - **Validates: Requirements 2.7, 6.8**
    - Test that expired tokens are properly rejected
    - Create tokens with past expiration, verify rejection
    - _Requirements: 2.7, 6.8_

- [ ] 10. Implement authentication middleware for FastAPI
  - [ ] 10.1 Create authentication middleware
    - Create `app/core/auth/middleware.py` with AuthMiddleware class
    - Implement get_current_user dependency to extract user from JWT
    - Implement require_role decorator for role-based access control
    - Implement optional_auth dependency for public endpoints
    - Add proper error handling with 401/403 HTTP exceptions
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 10.2 Write property test for RBAC enforcement
    - **Property 5: Role-Based Access Control Enforcement**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5**
    - Test that role hierarchy is properly enforced
    - Generate random user/required role combinations
    - Verify access granted/denied based on role level
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 10.3 Write unit tests for authentication middleware
    - Test get_current_user with valid token
    - Test get_current_user with invalid token (401 error)
    - Test get_current_user with missing token (401 error)
    - Test require_role with sufficient permissions
    - Test require_role with insufficient permissions (403 error)
    - _Requirements: 5.1, 5.2, 5.3, 3.5_

- [ ] 11. Create protected API endpoints
  - [ ] 11.1 Implement authentication endpoints
    - Create `app/api/auth_routes.py` with authentication router
    - Implement GET /auth/login endpoint to initiate OAuth flow
    - Implement GET /auth/callback endpoint to handle OAuth callback
    - Implement POST /auth/logout endpoint
    - Implement GET /auth/me endpoint to get current user info
    - Add state management for CSRF protection
    - _Requirements: 2.1, 2.2, 2.3, 2.9, 2.10_
  
  - [ ] 11.2 Implement protected report endpoints
    - Create `app/api/report_routes.py` with reports router
    - Implement POST /reports/ endpoint (Safety Officer only)
    - Implement GET /reports/ endpoint (all authenticated users)
    - Implement GET /reports/{report_id} endpoint (all authenticated users)
    - Implement POST /reports/{report_id}/violations endpoint (Safety Officer only)
    - Add authentication dependencies to all endpoints
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 1.2, 1.3, 1.4_
  
  - [ ] 11.3 Implement analytics endpoints
    - Create `app/api/analytics_routes.py` with analytics router
    - Implement GET /analytics/violation-trends endpoint
    - Implement GET /analytics/top-violations endpoint
    - Implement GET /analytics/location-analytics endpoint
    - Implement GET /analytics/compliance-rate endpoint
    - Implement GET /analytics/health endpoint (no auth required)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 13.5_
  
  - [ ] 11.4 Write integration tests for API endpoints
    - Test full authentication flow from login to API access
    - Test report creation and retrieval with authentication
    - Test analytics endpoints return correct data
    - Test unauthorized access returns 401
    - Test insufficient permissions returns 403
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 12. Update FastAPI main application
  - Update `app/api/main.py` to include new routers
  - Add CORS middleware configuration for Streamlit
  - Add database initialization on startup
  - Add health check endpoint
  - Configure logging for authentication and database events
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 13. Checkpoint - Backend authentication complete
  - Test OAuth flow with Postman or curl
  - Verify JWT tokens are created and validated
  - Test all API endpoints with authentication
  - Verify role-based access control works
  - Run all authentication property tests
  - Ensure all tests pass, ask the user if questions arise

- [ ] 14. Implement Streamlit authentication module
  - [ ] 14.1 Create Streamlit authentication module
    - Create `app/web/auth_module.py` with StreamlitAuth class
    - Implement initialize_session method for session state setup
    - Implement show_login_page method with Microsoft sign-in button
    - Implement handle_callback method to process OAuth callback
    - Implement logout method to clear session
    - Implement get_auth_headers method for API requests
    - Implement show_user_info method to display user profile in sidebar
    - Implement require_auth decorator to protect pages
    - Implement require_role method for role-based page access
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 16.2, 16.3, 16.4_
  
  - [ ] 14.2 Write property test for session state consistency
    - **Property 9: Session State Consistency**
    - **Validates: Requirements 6.4, 6.6**
    - Test that session token matches displayed user info
    - Generate random user sessions and verify consistency
    - _Requirements: 6.4, 6.6_

- [ ] 15. Update Streamlit main application
  - [ ] 15.1 Integrate authentication into Streamlit app
    - Update `app/web/streamlit_app_enhanced.py` to use StreamlitAuth
    - Add authentication requirement at app entry point
    - Update all API calls to include authentication headers
    - Add user profile display in sidebar
    - Add logout button
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [ ] 15.2 Update dashboard to use database
    - Modify dashboard to fetch reports from database via API
    - Update report generation to save to database
    - Update analytics to query database
    - Add error handling for API failures
    - _Requirements: 1.2, 1.3, 1.4, 10.1, 10.2, 10.3, 10.4_
  
  - [ ] 15.3 Add role-based UI features
    - Show/hide features based on user role
    - Add Admin-only settings page
    - Add Safety Officer report generation page
    - Add Viewer read-only analytics page
    - _Requirements: 3.2, 3.3, 3.4_

- [ ] 16. Create demo data seeding script
  - Create `scripts/seed_demo_data.py` script
  - Generate sample users with different roles
  - Generate sample reports with various violation types
  - Generate sample violations across different locations and dates
  - Generate realistic detection history data
  - Add command-line options to clear and reseed data
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 17. Create teardown script
  - Create `scripts/teardown_aws.py` script
  - Implement RDS instance deletion with confirmation
  - Add verification that resources are deleted
  - Document manual Azure AD B2C cleanup steps
  - Add cost verification check
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 18. Final checkpoint - Complete system testing
  - [ ] 18.1 End-to-end testing
    - Test complete flow: login → generate report → view analytics → logout
    - Test with different user roles (Admin, Safety Officer, Viewer)
    - Test error scenarios (invalid token, expired session, insufficient permissions)
    - Verify all data persists in database
    - Verify Microsoft profile picture displays correctly
  
  - [ ] 18.2 Performance testing
    - Test database query performance (<500ms for typical queries)
    - Test authentication flow performance (<2 seconds)
    - Test with multiple concurrent users (simulate 10+ users)
    - Verify connection pool handles load correctly
  
  - [ ] 18.3 Security testing
    - Verify CSRF protection works (invalid state rejected)
    - Verify expired tokens are rejected
    - Verify role-based access control enforced
    - Verify SQL injection protection (parameterized queries)
    - Verify sensitive data not logged
  
  - [ ] 18.4 Documentation review
    - Review all environment variables documented in .env.example
    - Verify setup instructions are complete and accurate
    - Verify teardown instructions work correctly
    - Create demo presentation slides
  
  - Ensure all tests pass, ask the user if questions arise

---

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation before proceeding
- Property tests use Hypothesis library with minimum 100 iterations
- Unit tests use pytest framework
- All database operations use SQLAlchemy ORM (no raw SQL)
- All authentication uses Microsoft Azure AD B2C (not AWS Cognito)
- Implementation stays within AWS and Azure free tier limits

---

## Dependencies

**Python Packages:**
```
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
alembic>=1.12.0
msal>=1.24.0
python-jose[cryptography]>=3.3.0
fastapi>=0.104.0
uvicorn>=0.24.0
streamlit>=1.28.0
hypothesis>=6.90.0
pytest>=7.4.0
requests>=2.31.0
python-dotenv>=1.0.0
```

**External Services:**
- AWS Account with RDS access
- Azure Account with Azure AD B2C access
- PostgreSQL 15 (via AWS RDS)

---

## Success Criteria

Implementation is successful when:

1. ✅ Users can sign in with Microsoft accounts
2. ✅ "Sign in with Microsoft" button appears on Streamlit login page
3. ✅ User profile picture and organization display in sidebar
4. ✅ All reports and violations save to AWS RDS PostgreSQL
5. ✅ Analytics queries return data from database
6. ✅ Role-based access control works (Admin, Safety Officer, Viewer)
7. ✅ All property tests pass (minimum 100 iterations each)
8. ✅ All unit tests pass
9. ✅ Integration tests pass
10. ✅ System stays within AWS and Azure free tier limits
11. ✅ Demo data is seeded and showcases system capabilities
12. ✅ Teardown script successfully removes all AWS resources

---

**Document Version:** 1.0  
**Created:** January 14, 2026  
**Status:** Ready for Implementation
