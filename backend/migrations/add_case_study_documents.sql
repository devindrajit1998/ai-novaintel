-- Migration: Add case_study_documents table and update case_studies table
-- Date: 2024-01-XX

-- Add matching_case_studies column to insights table (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'insights' 
        AND column_name = 'matching_case_studies'
    ) THEN
        ALTER TABLE insights ADD COLUMN matching_case_studies JSONB;
    END IF;
END $$;

-- Create ProcessingStatus enum type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processingstatus') THEN
        CREATE TYPE processingstatus AS ENUM ('pending', 'extracting', 'analyzing', 'indexing', 'completed', 'failed');
    END IF;
END $$;

-- Create case_study_documents table if it doesn't exist
CREATE TABLE IF NOT EXISTS case_study_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    extracted_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add new columns to case_study_documents if they don't exist
DO $$ 
BEGIN
    -- Add processing_status column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_study_documents' 
        AND column_name = 'processing_status'
    ) THEN
        ALTER TABLE case_study_documents ADD COLUMN processing_status processingstatus DEFAULT 'pending';
    END IF;
    
    -- Add error_message column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_study_documents' 
        AND column_name = 'error_message'
    ) THEN
        ALTER TABLE case_study_documents ADD COLUMN error_message TEXT;
    END IF;
    
    -- Add document_metadata column (rename from metadata if exists)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_study_documents' 
        AND column_name = 'document_metadata'
    ) THEN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'case_study_documents' 
            AND column_name = 'metadata'
        ) THEN
            ALTER TABLE case_study_documents RENAME COLUMN metadata TO document_metadata;
        ELSE
            ALTER TABLE case_study_documents ADD COLUMN document_metadata JSONB;
        END IF;
    END IF;
    
    -- Add case_study_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_study_documents' 
        AND column_name = 'case_study_id'
    ) THEN
        ALTER TABLE case_study_documents ADD COLUMN case_study_id INTEGER REFERENCES case_studies(id) ON DELETE SET NULL;
    END IF;
    
    -- Remove old 'processed' column if it exists (replaced by processing_status)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_study_documents' 
        AND column_name = 'processed'
    ) THEN
        ALTER TABLE case_study_documents DROP COLUMN processed;
    END IF;
END $$;

-- Update case_studies table with new columns
DO $$ 
BEGIN
    -- Add project_description column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' 
        AND column_name = 'project_description'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN project_description TEXT;
    END IF;
    
    -- Add case_study_document_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' 
        AND column_name = 'case_study_document_id'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN case_study_document_id INTEGER REFERENCES case_study_documents(id) ON DELETE SET NULL;
    END IF;
    
    -- Add indexed column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'case_studies' 
        AND column_name = 'indexed'
    ) THEN
        ALTER TABLE case_studies ADD COLUMN indexed BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_case_study_documents_user ON case_study_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_case_study_documents_processing_status ON case_study_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_case_study_documents_case_study_id ON case_study_documents(case_study_id);
CREATE INDEX IF NOT EXISTS idx_case_studies_document_id ON case_studies(case_study_document_id);
CREATE INDEX IF NOT EXISTS idx_case_studies_indexed ON case_studies(indexed);

-- Add comments
COMMENT ON TABLE case_study_documents IS 'Stores uploaded case study documents for training the AI system';
COMMENT ON COLUMN case_study_documents.processing_status IS 'Current processing status: pending, extracting, analyzing, indexing, completed, failed';
COMMENT ON COLUMN case_studies.indexed IS 'Whether this case study is indexed in RAG for similarity search';
