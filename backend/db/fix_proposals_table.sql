-- Fix proposals table to match the model
-- Add missing columns: sections, template_type, last_exported_at, export_format

-- Add sections column (JSONB for PostgreSQL)
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS sections JSONB;

-- Add template_type column
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS template_type VARCHAR(50) DEFAULT 'full';

-- Add last_exported_at column
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS last_exported_at TIMESTAMP;

-- Add export_format column
ALTER TABLE proposals 
ADD COLUMN IF NOT EXISTS export_format VARCHAR(10);

-- Update title to have NOT NULL constraint if it doesn't exist
ALTER TABLE proposals 
ALTER COLUMN title SET NOT NULL;

-- Set default for title if not set
UPDATE proposals 
SET title = 'Proposal' 
WHERE title IS NULL;

-- Migrate existing content to sections if content exists and sections doesn't
-- This handles the case where old proposals have 'content' instead of 'sections'
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'proposals' AND column_name = 'content'
    ) THEN
        -- Migrate content to sections format
        UPDATE proposals 
        SET sections = CASE 
            WHEN content IS NOT NULL AND sections IS NULL THEN
                jsonb_build_array(
                    jsonb_build_object(
                        'id', 1,
                        'title', 'Proposal Content',
                        'content', content::text,
                        'order', 0
                    )
                )
            ELSE sections
        END
        WHERE content IS NOT NULL AND sections IS NULL;
    END IF;
END $$;

-- Create index on project_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_proposals_project_id ON proposals(project_id);

