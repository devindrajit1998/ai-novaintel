# Database Schema Fix

## Problem

The `users` table has duplicate columns and mixed Supabase auth schema, causing 500 errors.

## Solution

You need to recreate the `users` table with the correct schema.

## Option 1: Using Supabase SQL Editor (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste the contents of `backend/db/fix_users_table.sql`
5. Click **Run**

**⚠️ WARNING**: This will delete all existing user data!

## Option 2: Using psql

```bash
psql "postgres://postgres.asecinomahhoylszccph:lItEofaSEGk8cpN6@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require" -f backend/db/fix_users_table.sql
```

## After Fixing

1. Restart your backend server
2. Try registering a user again
3. The 500 error should be resolved

## Verify Fix

Run:
```bash
cd backend
python check_db.py
```

You should see only these columns:
- id
- email
- full_name
- hashed_password
- role
- is_active
- email_verified
- email_verification_token
- email_verified_at
- created_at
- updated_at

