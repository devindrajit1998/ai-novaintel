# NovaIntel Setup Guide (Post-Supabase Migration)

This guide will help you set up NovaIntel after removing Supabase dependencies.

## Prerequisites

1. **PostgreSQL** - Install and running locally or remotely
2. **Python 3.8+** - For backend
3. **Node.js & npm** - For frontend (if needed)

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 2: Setup PostgreSQL Database

### Create Database

```bash
# Using psql
createdb novaintel

# Or using SQL
psql -U postgres
CREATE DATABASE novaintel;
```

### Run Migration

```bash
psql -d novaintel -f db/migration.sql
```

Or manually run the SQL from `db/migration.sql` in your PostgreSQL client.

## Step 3: Configure Environment Variables

Create `backend/.env` file:

```env
# Database - REQUIRED
DATABASE_URL=postgresql://user:password@localhost:5432/novaintel

# JWT - REQUIRED (generate secret key with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Vector Database - REQUIRED
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# LLM - REQUIRED
GEMINI_API_KEY=your-gemini-api-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx

# Email (Optional - for email verification)
# If not configured, verification links will be printed to console
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:8080

# CORS
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

### Generate Secret Key

```bash
openssl rand -hex 32
```

Copy the output to `SECRET_KEY` in your `.env` file.

## Step 4: Start the Backend Server

```bash
cd backend
python run.py
```

The server will start on `http://localhost:8000`

You should see:
- ✓ Database tables created/verified
- ✓ Gemini service ready
- ✓ Vector store ready: chroma

## Step 5: Ingest Training Data (Optional)

To add training documents to your vector database:

```bash
python scripts/ingest_data.py /path/to/your/documents [user_email]
```

Example:
```bash
python scripts/ingest_data.py ./training_docs admin@novaintel.com
```

This will:
1. Create an admin user (if doesn't exist)
2. Create a training project
3. Process all PDF/DOCX files in the directory
4. Build vector indexes for RAG

## Step 6: Test the API

### Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "Test User"
  }'
```

### Verify Email

Check console output for verification link, or configure SMTP to receive email.

Then visit:
```
http://localhost:8080/verify-email/{token}
```

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

You'll receive access and refresh tokens.

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Database Connection Error

- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL format: `postgresql://user:password@host:port/database`
- Check user has permissions on the database

### Vector Store Not Initializing

- Check `CHROMA_PERSIST_DIR` directory exists and is writable
- Verify `VECTOR_DB_TYPE=chroma` in `.env`

### Email Not Sending

- If SMTP not configured, verification links are printed to console
- Check SMTP credentials
- For Gmail, use App Password (not regular password)

### Import Errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## Directory Structure

```
backend/
├── chroma_db/          # Vector database (created automatically)
├── uploads/            # Uploaded RFP documents
├── scripts/
│   └── ingest_data.py  # Data ingestion script
└── .env                # Environment variables
```

## Next Steps

1. Configure frontend to point to `http://localhost:8000`
2. Test user registration and login
3. Upload RFP documents
4. Test RAG chat functionality
5. Build proposals

## Support

For issues, check:
- Backend logs in console
- Database connection status
- Vector store initialization messages
- API documentation at `/docs`

