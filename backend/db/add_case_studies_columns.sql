-- Add missing columns to case_studies table
-- This migration adds the missing columns that are defined in the CaseStudy model

-- Add user_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='case_studies' AND column_name='user_id'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN user_id INTEGER;
        -- Add foreign key constraint
        ALTER TABLE case_studies 
        ADD CONSTRAINT case_studies_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add project_description column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='case_studies' AND column_name='project_description'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN project_description TEXT;
    END IF;
END $$;

-- Add case_study_document_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='case_studies' AND column_name='case_study_document_id'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN case_study_document_id INTEGER;
        -- Add foreign key constraint if case_study_documents table exists
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='case_study_documents') THEN
            ALTER TABLE case_studies 
            ADD CONSTRAINT case_studies_case_study_document_id_fkey 
            FOREIGN KEY (case_study_document_id) REFERENCES case_study_documents(id) ON DELETE SET NULL;
        END IF;
    END IF;
END $$;

-- Add project_id column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='case_studies' AND column_name='project_id'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN project_id INTEGER;
        -- Add foreign key constraint
        ALTER TABLE case_studies 
        ADD CONSTRAINT case_studies_project_id_fkey 
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add indexed column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='case_studies' AND column_name='indexed'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN indexed BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Verify columns were added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name='case_studies' 
ORDER BY ordinal_position;

