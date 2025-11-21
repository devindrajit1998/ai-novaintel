# Complete Database Schema Fix

## Overview

This guide fixes all database schema mismatches in your NovaIntel project.

## Quick Fix (Recommended)

Run the comprehensive fix script that addresses all issues at once:

**File:** `backend/db/fix_all_tables.sql`

### Steps:

1. Go to **Supabase Dashboard** → **SQL Editor**
2. Copy the entire contents of `backend/db/fix_all_tables.sql`
3. Paste and click **Run**
4. Restart your backend server

## What Gets Fixed

### 1. `rfp_documents` Table
- ✅ Adds `extracted_text TEXT` column
- ✅ Adds `page_count INTEGER` column  
- ✅ Updates `file_size` from INTEGER to BIGINT

### 2. `insights` Table
- ✅ Adds `executive_summary TEXT` column
- ✅ Adds `tags JSONB` column
- ✅ Adds `ai_model_used TEXT` column
- ✅ Adds `analysis_timestamp TIMESTAMP` column
- ✅ Adds unique constraint on `project_id`

### 3. `case_studies` Table
- ✅ Adds `impact VARCHAR(255)` column (required)
- ✅ Ensures `industry` is NOT NULL

## Individual Fixes (If Needed)

If you prefer to run fixes individually:

1. **RFP Documents:** `backend/db/fix_rfp_documents.sql`
2. **Insights:** `backend/db/fix_insights.sql`
3. **Case Studies:** `backend/db/fix_case_studies.sql`

## Verification

After running the script, you should see output showing the table structures. Verify:

### rfp_documents columns:
- `extracted_text` (text)
- `page_count` (integer)
- `file_size` (bigint)

### insights columns:
- `executive_summary` (text)
- `tags` (jsonb)
- `ai_model_used` (text)
- `analysis_timestamp` (timestamp without time zone)

### case_studies columns:
- `impact` (varchar(255), NOT NULL)
- `industry` (varchar(100), NOT NULL)

## After Running

1. ✅ Restart backend server
2. ✅ Try uploading RFP documents
3. ✅ Try fetching insights
4. ✅ All errors should be resolved

## Notes

- All scripts are **idempotent** (safe to run multiple times)
- They use `DO $$` blocks to check if columns exist before adding
- No data will be lost - only adds missing columns

