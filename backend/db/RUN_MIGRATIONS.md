# Database Migration Instructions

## Quick Fix - Run All Migrations

Run the comprehensive migration script that fixes all missing columns:

### Option 1: Using Supabase SQL Editor (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste the entire contents of `backend/db/migrate_all_tables.sql`
5. Click **Run**

### Option 2: Using psql Command Line

```bash
psql "YOUR_DATABASE_URL" -f backend/db/migrate_all_tables.sql
```

Replace `YOUR_DATABASE_URL` with your actual database connection string.

### Option 3: Run Individual Migrations

If you prefer to run migrations separately:

1. **User Settings**: `backend/db/add_user_settings_columns.sql`
2. **Notifications**: `backend/db/add_notifications_columns.sql`
3. **Case Studies**: `backend/db/add_case_studies_columns.sql`

## What Gets Fixed

### Users Table
- ✅ `proposal_tone` - User's preferred proposal tone
- ✅ `ai_response_style` - AI response style preference
- ✅ `secure_mode` - PII sanitization setting
- ✅ `auto_save_insights` - Auto-save insights setting
- ✅ `theme_preference` - UI theme preference

### Notifications Table
- ✅ `type` - Notification type (success, error, info, warning)
- ✅ `title` - Notification title
- ✅ `message` - Notification message
- ✅ `status` - Notification status (pending, processing, completed, failed)
- ✅ `is_read` - Read status
- ✅ `read_at` - When notification was read
- ✅ `metadata` - Additional metadata (JSON)

### Case Studies Table
- ✅ `user_id` - Creator of the case study
- ✅ `project_description` - Detailed project description
- ✅ `case_study_document_id` - Link to source document
- ✅ `project_id` - Link to source project
- ✅ `indexed` - Whether indexed in RAG

## Verification

After running migrations, verify with:

```sql
-- Check users table
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name='users' 
AND column_name IN ('proposal_tone', 'ai_response_style', 'secure_mode', 'auto_save_insights', 'theme_preference')
ORDER BY column_name;

-- Check notifications table
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name='notifications' 
ORDER BY ordinal_position;

-- Check case_studies table
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name='case_studies' 
ORDER BY ordinal_position;
```

## Auto-Migration (Alternative)

The migrations also run automatically on server startup. If you prefer, just restart your server and the migrations will run automatically. Check the console output for migration status.

## Troubleshooting

### Error: "relation does not exist"
- The table doesn't exist yet. It will be created automatically by SQLAlchemy on server startup.

### Error: "column already exists"
- The column is already there. This is safe to ignore - the migration checks before adding.

### Error: "foreign key constraint"
- Make sure the referenced tables (users, projects, case_study_documents) exist first.

