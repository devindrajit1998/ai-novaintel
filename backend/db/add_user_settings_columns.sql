-- Add user settings columns to users table
-- This migration adds the missing columns that are defined in the User model

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

-- Add company_name column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='company_name'
    ) THEN
        ALTER TABLE users ADD COLUMN company_name VARCHAR(255);
    END IF;
END $$;

-- Add company_logo column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='company_logo'
    ) THEN
        ALTER TABLE users ADD COLUMN company_logo VARCHAR(500);
    END IF;
END $$;

-- Verify columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name='users' 
AND column_name IN ('proposal_tone', 'ai_response_style', 'secure_mode', 'auto_save_insights', 'theme_preference', 'company_name', 'company_logo')
ORDER BY column_name;

