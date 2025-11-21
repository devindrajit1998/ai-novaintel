# Fix RFP Documents Table Schema

## Problem

The `rfp_documents` table is missing the `extracted_text` and `page_count` columns, causing upload errors:

```
column "extracted_text" of relation "rfp_documents" does not exist
```

## Solution

Run the SQL migration script to add the missing columns.

## Option 1: Using Supabase SQL Editor (Recommended)

1. Go to https://supabase.com/dashboard
2. Select your project
3. Open **SQL Editor**
4. Copy and paste the contents of `backend/db/fix_rfp_documents.sql`
5. Click **Run**

## Option 2: Using psql

```bash
psql "postgres://postgres.asecinomahhoylszccph:lItEofaSEGk8cpN6@aws-1-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require" -f backend/db/fix_rfp_documents.sql
```

## What the Script Does

1. Adds `extracted_text TEXT` column (nullable) - stores extracted text from PDFs/DOCX
2. Adds `page_count INTEGER` column (nullable) - stores number of pages
3. Updates `file_size` from INTEGER to BIGINT (for large files)

## After Running

1. Restart your backend server
2. Try uploading an RFP document again
3. The error should be resolved

## Verify

The script will output the table structure after running. You should see:
- `extracted_text` (text)
- `page_count` (integer)
- `file_size` (bigint)

