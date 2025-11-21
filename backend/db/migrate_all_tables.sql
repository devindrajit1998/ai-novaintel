-- ============================================================================
-- Complete Database Migration Script
-- Run this to add all missing columns to existing tables
-- ============================================================================

-- ============================================================================
-- 1. Add User Settings Columns to users table
-- ============================================================================

-- Add proposal_tone column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='proposal_tone'
    ) THEN
        ALTER TABLE users ADD COLUMN proposal_tone VARCHAR(50) DEFAULT 'professional';
    END IF;
END $$;

-- Add ai_response_style column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='ai_response_style'
    ) THEN
        ALTER TABLE users ADD COLUMN ai_response_style VARCHAR(50) DEFAULT 'balanced';
    END IF;
END $$;

-- Add secure_mode column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='secure_mode'
    ) THEN
        ALTER TABLE users ADD COLUMN secure_mode BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add auto_save_insights column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='auto_save_insights'
    ) THEN
        ALTER TABLE users ADD COLUMN auto_save_insights BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Add theme_preference column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='theme_preference'
    ) THEN
        ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'light';
    END IF;
END $$;

-- ============================================================================
-- 2. Add Missing Columns to notifications table
-- ============================================================================

-- Add type column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='type'
    ) THEN
        ALTER TABLE notifications ADD COLUMN type VARCHAR(50) DEFAULT 'info';
        -- Update existing rows
        UPDATE notifications SET type = 'info' WHERE type IS NULL;
        -- Make NOT NULL
        ALTER TABLE notifications ALTER COLUMN type SET NOT NULL;
    END IF;
END $$;

-- Add title column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='title'
    ) THEN
        ALTER TABLE notifications ADD COLUMN title VARCHAR(255) DEFAULT 'Notification';
        -- Update existing rows
        UPDATE notifications SET title = 'Notification' WHERE title IS NULL OR title = '';
        -- Make NOT NULL
        ALTER TABLE notifications ALTER COLUMN title SET NOT NULL;
    END IF;
END $$;

-- Add message column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='message'
    ) THEN
        ALTER TABLE notifications ADD COLUMN message TEXT DEFAULT '';
        -- Update existing rows
        UPDATE notifications SET message = '' WHERE message IS NULL;
        -- Make NOT NULL
        ALTER TABLE notifications ALTER COLUMN message SET NOT NULL;
    END IF;
END $$;

-- Add status column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='status'
    ) THEN
        ALTER TABLE notifications ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
    END IF;
END $$;

-- Add is_read column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='is_read'
    ) THEN
        ALTER TABLE notifications ADD COLUMN is_read BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add read_at column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='read_at'
    ) THEN
        ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Add metadata column (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='metadata'
    ) THEN
        ALTER TABLE notifications ADD COLUMN metadata JSON;
    END IF;
END $$;

-- ============================================================================
-- 3. Add Missing Columns to case_studies table
-- ============================================================================

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
        -- Add foreign key constraint if table exists
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

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify users table columns
SELECT 'users table columns:' as info;
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name='users' 
AND column_name IN ('proposal_tone', 'ai_response_style', 'secure_mode', 'auto_save_insights', 'theme_preference')
ORDER BY column_name;

-- Verify notifications table columns
SELECT 'notifications table columns:' as info;
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name='notifications' 
ORDER BY ordinal_position;

-- Verify case_studies table columns
SELECT 'case_studies table columns:' as info;
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name='case_studies' 
ORDER BY ordinal_position;

