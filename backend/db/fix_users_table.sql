-- Fix users table - Remove Supabase auth columns and keep only our custom columns
-- Run this in your PostgreSQL database

-- First, backup existing data if needed
-- CREATE TABLE users_backup AS SELECT * FROM users;

-- Drop the existing users table (WARNING: This will delete all user data!)
DROP TABLE IF EXISTS users CASCADE;

-- Recreate users table with correct schema
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'presales_manager',
    is_active BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(500),
    email_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recreate indexes
CREATE INDEX idx_users_email ON users(email);

-- Recreate foreign key constraints for projects
ALTER TABLE projects ADD CONSTRAINT projects_owner_id_fkey 
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

