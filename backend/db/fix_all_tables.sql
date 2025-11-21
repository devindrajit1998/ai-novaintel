-- Comprehensive Database Schema Fix
-- This script fixes all schema mismatches for the NovaIntel project
-- Run this in your PostgreSQL database (Supabase SQL Editor)

-- ============================================================================
-- 1. Fix rfp_documents table
-- ============================================================================

-- Add extracted_text column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rfp_documents' AND column_name = 'extracted_text'
    ) THEN
        ALTER TABLE rfp_documents ADD COLUMN extracted_text TEXT;
    END IF;
END $$;

-- Add page_count column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rfp_documents' AND column_name = 'page_count'
    ) THEN
        ALTER TABLE rfp_documents ADD COLUMN page_count INTEGER;
    END IF;
END $$;

-- Update file_size to BIGINT if it's currently INTEGER
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'rfp_documents' 
        AND column_name = 'file_size' 
        AND data_type = 'integer'
    ) THEN
        ALTER TABLE rfp_documents ALTER COLUMN file_size TYPE BIGINT;
    END IF;
END $$;

-- ============================================================================
-- 2. Fix insights table
-- ============================================================================

-- Add executive_summary column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insights' AND column_name = 'executive_summary'
    ) THEN
        ALTER TABLE insights ADD COLUMN executive_summary TEXT;
    END IF;
END $$;

-- Add tags column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insights' AND column_name = 'tags'
    ) THEN
        ALTER TABLE insights ADD COLUMN tags JSONB;
    END IF;
END $$;

-- Add ai_model_used column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insights' AND column_name = 'ai_model_used'
    ) THEN
        ALTER TABLE insights ADD COLUMN ai_model_used TEXT;
    END IF;
END $$;

-- Add analysis_timestamp column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insights' AND column_name = 'analysis_timestamp'
    ) THEN
        ALTER TABLE insights ADD COLUMN analysis_timestamp TIMESTAMP;
    END IF;
END $$;

-- Add unique constraint on project_id if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'insights_project_id_key'
    ) THEN
        ALTER TABLE insights ADD CONSTRAINT insights_project_id_key UNIQUE (project_id);
    END IF;
END $$;

-- ============================================================================
-- 3. Fix case_studies table
-- ============================================================================

-- Add impact column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' AND column_name = 'impact'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN impact VARCHAR(255);
        -- Set a default value for existing rows if needed
        UPDATE case_studies SET impact = 'N/A' WHERE impact IS NULL;
        -- Make it NOT NULL after setting defaults
        ALTER TABLE case_studies ALTER COLUMN impact SET NOT NULL;
    END IF;
END $$;

-- Ensure industry is NOT NULL if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' AND column_name = 'industry'
        AND is_nullable = 'YES'
    ) THEN
        -- Set default for existing NULL values
        UPDATE case_studies SET industry = 'General' WHERE industry IS NULL;
        ALTER TABLE case_studies ALTER COLUMN industry SET NOT NULL;
    END IF;
END $$;

-- Remove old columns if they exist (optional cleanup)
-- Uncomment these if you want to remove unused columns:
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'case_studies' AND column_name = 'client_name'
--     ) THEN
--         ALTER TABLE case_studies DROP COLUMN client_name;
--     END IF;
-- END $$;
-- 
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'case_studies' AND column_name = 'challenges'
--     ) THEN
--         ALTER TABLE case_studies DROP COLUMN challenges;
--     END IF;
-- END $$;
-- 
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'case_studies' AND column_name = 'solution'
--     ) THEN
--         ALTER TABLE case_studies DROP COLUMN solution;
--     END IF;
-- END $$;
-- 
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'case_studies' AND column_name = 'results'
--     ) THEN
--         ALTER TABLE case_studies DROP COLUMN results;
--     END IF;
-- END $$;

-- ============================================================================
-- 4. Summary - Show all table structures
-- ============================================================================

SELECT 'rfp_documents' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'rfp_documents' 
ORDER BY ordinal_position;

SELECT 'insights' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'insights' 
ORDER BY ordinal_position;

SELECT 'case_studies' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'case_studies' 
ORDER BY ordinal_position;

