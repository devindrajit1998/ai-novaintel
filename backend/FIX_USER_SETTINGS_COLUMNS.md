# Fix Missing User Settings Columns

## Problem

The `users` table is missing several columns that are defined in the User model:
- `proposal_tone`
- `ai_response_style`
- `secure_mode`
- `auto_save_insights`
- `theme_preference`

This causes errors like:
```
column users.proposal_tone does not exist
```

## Solution

### Option 1: Automatic Migration (Recommended)

The server will automatically add missing columns on startup. Just restart your backend server:

```bash
cd backend
python run.py
```

You should see messages like:
```
✓ Added column: proposal_tone
✓ Added column: ai_response_style
...
✓ Migration complete: Added 5 column(s) to users table
```

### Option 2: Manual SQL Migration

If you prefer to run the migration manually, use the SQL script:

**Using Supabase SQL Editor:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste the contents of `backend/db/add_user_settings_columns.sql`
5. Click **Run**

**Using psql:**
```bash
psql "YOUR_DATABASE_URL" -f backend/db/add_user_settings_columns.sql
```

### Option 3: Python Script

Run the Python migration script (requires virtual environment):

```bash
cd backend
# Activate your virtual environment first
python scripts/add_user_settings_columns.py
```

## Verify Fix

After running the migration, verify the columns exist:

```sql
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name='users' 
AND column_name IN ('proposal_tone', 'ai_response_style', 'secure_mode', 'auto_save_insights', 'theme_preference')
ORDER BY column_name;
```

You should see all 5 columns listed.

## After Fixing

1. Restart your backend server
2. Try logging in again
3. The error should be resolved

