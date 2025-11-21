-- Fix insights table - Add missing columns and update schema
-- Run this in your PostgreSQL database

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

-- Remove old columns if they exist (optional - only if you want to clean up)
-- Uncomment these if you want to remove the old columns:
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'insights' AND column_name = 'rfp_summary'
--     ) THEN
--         ALTER TABLE insights DROP COLUMN rfp_summary;
--     END IF;
-- END $$;
-- 
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'insights' AND column_name = 'matching_case_studies'
--     ) THEN
--         ALTER TABLE insights DROP COLUMN matching_case_studies;
--     END IF;
-- END $$;
-- 
-- DO $$ 
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM information_schema.columns 
--         WHERE table_name = 'insights' AND column_name = 'proposal_draft'
--     ) THEN
--         ALTER TABLE insights DROP COLUMN proposal_draft;
--     END IF;
-- END $$;

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

-- Verify columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'insights' 
ORDER BY ordinal_position;

