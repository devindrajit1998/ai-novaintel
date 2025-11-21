-- Fix case_studies table - Add missing impact column
-- Run this in your PostgreSQL database

-- Add impact column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' AND column_name = 'impact'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN impact VARCHAR(255);
        -- Set a default value for existing rows
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

-- Verify columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'case_studies' 
ORDER BY ordinal_position;

