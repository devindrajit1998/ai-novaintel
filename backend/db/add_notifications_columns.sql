-- Add missing columns to notifications table
-- This migration adds the missing columns that are defined in the Notification model

-- Add type column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='type'
    ) THEN
        ALTER TABLE notifications ADD COLUMN type VARCHAR(50) DEFAULT 'info' NOT NULL;
    END IF;
END $$;

-- Add title column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='title'
    ) THEN
        ALTER TABLE notifications ADD COLUMN title VARCHAR(255) NOT NULL;
        -- Set default for existing rows
        UPDATE notifications SET title = 'Notification' WHERE title IS NULL OR title = '';
    END IF;
END $$;

-- Add message column
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='message'
    ) THEN
        ALTER TABLE notifications ADD COLUMN message TEXT NOT NULL;
        -- Set default for existing rows
        UPDATE notifications SET message = '' WHERE message IS NULL;
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

-- Add metadata column (if it doesn't exist as JSON)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='notifications' AND column_name='metadata'
    ) THEN
        ALTER TABLE notifications ADD COLUMN metadata JSON;
    END IF;
END $$;

-- Verify columns were added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name='notifications' 
ORDER BY ordinal_position;

