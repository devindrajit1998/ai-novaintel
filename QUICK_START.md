# Quick Start Guide

## ⚠️ IMPORTANT: Create Backend .env File

You need to manually create `backend/.env` file with the following content:

```env
# Database - Update with your PostgreSQL credentials
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/novaintel

# JWT
SECRET_KEY=cd572dac2913af842bd63f04dd16d04f8c56b036eb1e8ec6064cbe7a3d7ed537
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# LLM - REQUIRED: Get from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
FRONTEND_URL=http://localhost:8080

# CORS
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

## Setup PostgreSQL Database

1. Install PostgreSQL if not already installed
2. Create database:
   ```sql
   CREATE DATABASE novaintel;
   ```
3. Run migration:
   ```bash
   psql -d novaintel -f backend/db/migration.sql
   ```

## Start the Project

### Terminal 1 - Backend
```bash
cd backend
python run.py
```

### Terminal 2 - Frontend
```bash
npm run dev
```

## Access Points

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

