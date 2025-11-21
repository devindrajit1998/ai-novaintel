# Database Migrations Fixed

## Issues Fixed

### 1. Missing `notifications.type` Column
**Error**: `column notifications.type does not exist`

**Solution**: Created auto-migration script that adds missing columns to notifications table:
- `type` (VARCHAR(50), NOT NULL, default: 'info')
- `title` (VARCHAR(255), NOT NULL)
- `message` (TEXT, NOT NULL)
- `status` (VARCHAR(20), default: 'pending')
- `is_read` (BOOLEAN, default: FALSE)
- `read_at` (TIMESTAMP WITH TIME ZONE, nullable)
- `metadata` (JSON, nullable)

### 2. Missing `case_studies.project_id` Column
**Error**: `column case_studies.project_id does not exist`

**Solution**: Created auto-migration script that adds missing columns to case_studies table:
- `user_id` (INTEGER, nullable, FK to users)
- `project_description` (TEXT, nullable)
- `case_study_document_id` (INTEGER, nullable, FK to case_study_documents)
- `project_id` (INTEGER, nullable, FK to projects)
- `indexed` (BOOLEAN, default: FALSE)

Also adds foreign key constraints automatically.

## Files Created

1. **backend/db/migrate_notifications.py** - Auto-migration for notifications table
2. **backend/db/migrate_case_studies.py** - Auto-migration for case_studies table
3. **backend/db/add_notifications_columns.sql** - Manual SQL migration for notifications
4. **backend/db/add_case_studies_columns.sql** - Manual SQL migration for case_studies

## How It Works

The migrations run automatically on server startup in `main.py`:
1. Tables are created/verified via `Base.metadata.create_all()`
2. User settings columns are migrated
3. Notifications columns are migrated
4. Case studies columns are migrated

## Manual Migration (Optional)

If you prefer to run migrations manually:

**Using Supabase SQL Editor:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste contents of:
   - `backend/db/add_notifications_columns.sql`
   - `backend/db/add_case_studies_columns.sql`
5. Click **Run**

**Using psql:**
```bash
psql "YOUR_DATABASE_URL" -f backend/db/add_notifications_columns.sql
psql "YOUR_DATABASE_URL" -f backend/db/add_case_studies_columns.sql
```

## After Restart

When you restart the server, you should see:
```
✓ Database tables created/verified
✓ All user settings columns already exist
✓ Added column to notifications: type
✓ Added column to notifications: title
...
✓ Migration complete: Added X column(s) to notifications table
✓ Added column to case_studies: project_id
...
✓ Migration complete: Added X column(s) to case_studies table
```

The errors should be resolved after the migrations run.

