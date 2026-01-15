# Alembic Database Migrations Guide

## Overview

This project uses Alembic for database schema migrations. Alembic tracks changes to the database schema over time and allows you to upgrade or downgrade the database to any version.

## Configuration

- **Configuration file**: `alembic.ini`
- **Migration scripts**: `alembic/versions/`
- **Environment setup**: `alembic/env.py`

The database URL is automatically loaded from the `DATABASE_URL` environment variable in `.env`.

## Current Migrations

### Initial Schema (72147ce4c0a5)

Creates all base tables with indexes:

**Tables:**
- `users` - User accounts with Microsoft SSO integration
- `reports` - Safety compliance reports
- `violations` - Safety violations detected
- `detection_history` - PPE detection history

**Indexes:**
- `users`: email, microsoft_user_id (unique)
- `reports`: timestamp, location, report_id (unique), user_id+timestamp, timestamp+location
- `violations`: violation_type, timestamp, location, report_id, type+timestamp, location+timestamp
- `detection_history`: timestamp, user_id+timestamp

## Common Commands

### Check current migration version
```bash
alembic current
```

### View migration history
```bash
alembic history
```

### Upgrade to latest version
```bash
alembic upgrade head
```

### Upgrade to specific version
```bash
alembic upgrade <revision_id>
```

### Downgrade one version
```bash
alembic downgrade -1
```

### Downgrade to specific version
```bash
alembic downgrade <revision_id>
```

### Create new migration (auto-generate)
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create empty migration (manual)
```bash
alembic revision -m "Description of changes"
```

## Creating New Migrations

1. Make changes to your SQLAlchemy models in `app/core/database/models.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add new column to users"
   ```
3. Review the generated migration in `alembic/versions/`
4. Edit if necessary (Alembic doesn't catch everything)
5. Apply migration:
   ```bash
   alembic upgrade head
   ```

## Best Practices

1. **Always review auto-generated migrations** - Alembic may miss some changes
2. **Test migrations on development database first**
3. **Never edit applied migrations** - Create a new migration instead
4. **Keep migrations small and focused** - One logical change per migration
5. **Add comments** - Explain complex migrations
6. **Test both upgrade and downgrade** - Ensure rollback works

## Troubleshooting

### Migration out of sync
If your database is out of sync with migrations:
```bash
# Check current version
alembic current

# Stamp database with current version (if tables exist but alembic_version is wrong)
alembic stamp head
```

### Reset database (development only)
```bash
# Drop all tables
python scripts/drop_all_tables.py

# Recreate from migrations
alembic upgrade head
```

### View SQL without applying
```bash
alembic upgrade head --sql
```

## Migration File Structure

```python
"""Description

Revision ID: abc123
Revises: xyz789
Create Date: 2026-01-15 09:11:39
"""

def upgrade() -> None:
    # Changes to apply
    op.create_table(...)
    op.add_column(...)

def downgrade() -> None:
    # Changes to revert
    op.drop_column(...)
    op.drop_table(...)
```

## Index Management

All performance indexes are included in the initial schema migration:

- **Timestamp indexes**: For time-based queries and analytics
- **Location indexes**: For location-based filtering
- **Foreign key indexes**: For join performance
- **Unique indexes**: For data integrity (microsoft_user_id, report_id)
- **Composite indexes**: For common query patterns (user_id+timestamp, location+timestamp)

## Notes

- Database URL is loaded from `DATABASE_URL` environment variable
- All models must be imported in `alembic/env.py` for autogenerate to work
- MySQL/Aurora specific features are handled automatically
- Connection pooling is disabled during migrations (uses NullPool)

## Related Files

- `app/core/database/models.py` - SQLAlchemy models
- `app/core/database/connection.py` - Database connection manager
- `scripts/drop_all_tables.py` - Drop all tables (development)
- `scripts/check_existing_tables.py` - List current tables
- `scripts/verify_indexes.py` - Verify indexes are created
