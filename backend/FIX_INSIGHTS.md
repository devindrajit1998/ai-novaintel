# Fix Insights Table Schema

## Problem

The `insights` table is missing required columns, causing errors when fetching insights:

```
column insights.executive_summary does not exist
```

## Solution

Run the SQL migration script to add the missing columns.

## Option 1: Using Supabase SQL Editor (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste the contents of `backend/db/fix_insights.sql`
5. Click **Run**

## Option 2: Using psql

```bash
psql "postgres://postgres.asecinomahhoylszccph:lItEofaSEGk8cpN6@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require" -f backend/db/fix_insights.sql
```

## What the Script Does

1. Adds `executive_summary TEXT` - Executive summary of insights
2. Adds `tags JSONB` - Tags/keywords for the insights
3. Adds `ai_model_used TEXT` - Which AI model was used for analysis
4. Adds `analysis_timestamp TIMESTAMP` - When the analysis was performed
5. Adds unique constraint on `project_id` (one insight per project)

## After Running

1. Restart your backend server
2. Try fetching insights again
3. The error should be resolved

## Verify

The script will output the table structure after running. You should see:
- `executive_summary` (text)
- `tags` (jsonb)
- `ai_model_used` (text)
- `analysis_timestamp` (timestamp without time zone)

