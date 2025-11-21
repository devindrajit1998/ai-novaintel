-- Fix rfp_documents table - Add missing columns
-- Run this in your PostgreSQL database

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

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'rfp_documents' 
ORDER BY ordinal_position;

