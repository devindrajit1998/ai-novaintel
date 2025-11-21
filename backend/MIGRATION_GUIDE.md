# Migration Guide: Removing Supabase

This guide documents the migration from Supabase to a self-hosted solution with custom authentication, PostgreSQL database, and Chroma vector store.

## Changes Made

### 1. Authentication
- **Removed**: Supabase Auth
- **Added**: Custom JWT-based authentication with email verification
- **Files Changed**:
  - `utils/security.py` - Added email verification token functions
  - `utils/dependencies.py` - Custom JWT token verification
  - `api/routers/auth.py` - Custom registration/login endpoints
  - `utils/email_service.py` - Email verification service
  - `models/user.py` - Added email verification fields

### 2. Database
- **Removed**: Supabase database client
- **Added**: Direct PostgreSQL connection via SQLAlchemy
- **Files Changed**:
  - `db/database.py` - Direct PostgreSQL connection
  - `db/migration.sql` - Database schema migration file

### 3. Vector Database
- **Removed**: Supabase pgvector
- **Added**: Chroma vector database
- **Files Changed**:
  - `rag/vector_store.py` - Chroma integration

### 4. File Storage
- **Removed**: Supabase Storage
- **Added**: Local filesystem storage
- **Files Changed**:
  - `api/routers/upload.py` - Local file storage

### 5. Configuration
- **Removed**: All Supabase-related environment variables
- **Added**: New configuration for PostgreSQL, Chroma, and email
- **Files Changed**:
  - `utils/config.py` - Updated configuration

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database

```bash
# Create database
createdb novaintel

# Run migration
psql -d novaintel -f db/migration.sql
```

### 3. Configure Environment Variables

Create or update `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/novaintel

# JWT
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# LLM
GEMINI_API_KEY=your-gemini-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx

# Email (optional - for email verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:8080

# CORS
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

### 4. Generate Secret Key

```bash
openssl rand -hex 32
```

### 5. Start the Server

```bash
python run.py
```

## Data Ingestion

To ingest training data into the vector database:

```bash
python scripts/ingest_data.py /path/to/your/documents [user_email]
```

This will:
1. Create or use an admin user
2. Create a training project
3. Process all PDF/DOCX files in the directory
4. Build vector indexes for each document

## API Changes

### Authentication Endpoints

- `POST /auth/register` - Register new user (requires email verification)
- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token
- `GET /auth/verify-email/{token}` - Verify email address

### Token Format

Tokens are now standard JWTs with the following payload:
```json
{
  "sub": "user@example.com",
  "email": "user@example.com",
  "user_id": 1,
  "type": "access",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Migration Checklist

- [x] Remove Supabase dependencies from requirements.txt
- [x] Update configuration to remove Supabase settings
- [x] Implement custom JWT authentication
- [x] Update database connection to use direct PostgreSQL
- [x] Replace Supabase Storage with local filesystem
- [x] Replace Supabase pgvector with Chroma
- [x] Update all routers to remove Supabase references
- [x] Create database migration script
- [x] Create data ingestion script

## Notes

- Email verification is optional but recommended. If SMTP is not configured, verification links will be printed to console.
- Chroma database is stored locally in `./chroma_db` directory.
- Uploaded files are stored in `./uploads` directory organized by project.
- All authentication is now handled by your own JWT tokens.
