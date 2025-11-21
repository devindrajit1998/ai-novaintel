-- NovaIntel Supabase Database Schema
-- Run this in Supabase SQL Editor after creating your project

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector"; -- For pgvector (optional, if using vector search)

-- Users table (integrated with Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL DEFAULT 'supabase_auth',
    role VARCHAR(50) DEFAULT 'presales_manager',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    project_type VARCHAR(50) NOT NULL DEFAULT 'new',
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RFP Documents table
CREATE TABLE IF NOT EXISTS rfp_documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    extracted_text TEXT,
    page_count INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insights table
CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    project_id INTEGER UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    executive_summary TEXT,
    challenges JSONB,
    value_propositions JSONB,
    discovery_questions JSONB,
    tags JSONB,
    ai_model_used TEXT,
    analysis_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proposals table
CREATE TABLE IF NOT EXISTS proposals (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'Proposal',
    sections JSONB,
    template_type VARCHAR(50) DEFAULT 'full',
    last_exported_at TIMESTAMP,
    export_format VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Case Studies table
CREATE TABLE IF NOT EXISTS case_studies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    impact VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_rfp_documents_project_id ON rfp_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_insights_project_id ON insights(project_id);
CREATE INDEX IF NOT EXISTS idx_proposals_project_id ON proposals(project_id);
CREATE INDEX IF NOT EXISTS idx_case_studies_industry ON case_studies(industry);

-- Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE rfp_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_studies ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
-- These policies use Supabase Auth.uid() to match user email

-- Users policy: users can read their own record
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (auth.email() = email);

-- Projects policy: users can only access their own projects
CREATE POLICY "Users can manage own projects" ON projects
    FOR ALL USING (
        owner_id IN (
            SELECT id FROM users WHERE email = auth.email()
        )
    );

-- RFP Documents policy: users can access documents for their projects
CREATE POLICY "Users can access own RFP documents" ON rfp_documents
    FOR ALL USING (
        project_id IN (
            SELECT p.id FROM projects p
            JOIN users u ON p.owner_id = u.id
            WHERE u.email = auth.email()
        )
    );

-- Insights policy: users can access insights for their projects
CREATE POLICY "Users can access own insights" ON insights
    FOR ALL USING (
        project_id IN (
            SELECT p.id FROM projects p
            JOIN users u ON p.owner_id = u.id
            WHERE u.email = auth.email()
        )
    );

-- Proposals policy: users can access proposals for their projects
CREATE POLICY "Users can access own proposals" ON proposals
    FOR ALL USING (
        project_id IN (
            SELECT p.id FROM projects p
            JOIN users u ON p.owner_id = u.id
            WHERE u.email = auth.email()
        )
    );

-- Case Studies: allow read access to all authenticated users
CREATE POLICY "Authenticated users can read case studies" ON case_studies
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can manage case studies" ON case_studies
    FOR ALL USING (auth.role() = 'authenticated');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_insights_updated_at BEFORE UPDATE ON insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_studies_updated_at BEFORE UPDATE ON case_studies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create storage bucket for RFP documents (run in Supabase Storage or via API)
-- Storage bucket will be created via the application code

COMMENT ON TABLE users IS 'User accounts integrated with Supabase Auth';
COMMENT ON TABLE projects IS 'Presales projects owned by users';
COMMENT ON TABLE rfp_documents IS 'Uploaded RFP documents for projects';
COMMENT ON TABLE insights IS 'AI-generated insights for projects';
COMMENT ON TABLE proposals IS 'Proposal documents for projects';
COMMENT ON TABLE case_studies IS 'Success stories and case studies';
