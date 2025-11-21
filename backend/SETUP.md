# Setup Guide - NovaIntel with Gemini & Supabase

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Supabase account (free tier works)
- Google AI Studio account (for Gemini API key)

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `backend/` directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=rfp-documents

# Gemini API
GEMINI_API_KEY=your-gemini-api-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Database URL (can be auto-constructed from Supabase)
DATABASE_URL=
```

### 4. Get API Keys

#### Supabase:
1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy:
   - Project URL → `SUPABASE_URL`
   - anon public key → `SUPABASE_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`

#### Gemini:
1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create API key
3. Copy to `GEMINI_API_KEY`

### 5. Setup Supabase Storage

1. Go to Supabase Dashboard → Storage
2. Create bucket: `rfp-documents`
3. Set to Private (or Public if needed)
4. Enable RLS if required

### 6. Run the Application

```bash
# Start backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend
npm run dev
```

### 7. Verify Setup

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

## Testing

### Test Authentication

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

### Test File Upload

```bash
# First, create a project and get project_id
# Then upload a file:
curl -X POST "http://localhost:8000/upload/rfp?project_id=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@path/to/your/rfp.pdf"
```

### Test Workflow

```bash
curl -X POST http://localhost:8000/agents/run-all \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "rfp_document_id": 1
  }'
```

## Troubleshooting

### "Supabase not available"
- Check `.env` file exists and has correct values
- Verify Supabase project is active
- Check network connectivity

### "Gemini API key not configured"
- Verify `GEMINI_API_KEY` in `.env`
- Test API key at [Google AI Studio](https://aistudio.google.com)

### "Storage bucket not found"
- Create bucket `rfp-documents` in Supabase Storage
- Check bucket name matches `SUPABASE_STORAGE_BUCKET`

### "Authentication failed"
- Check Supabase Auth is enabled
- Verify email confirmation settings (may need to disable for testing)
- Check user exists in Supabase Auth dashboard

### Database Connection Issues
- If using Supabase, database URL is optional
- SQLAlchemy will use Supabase client if URL not provided
- For direct PostgreSQL, set `DATABASE_URL` with format:
  `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

## Production Deployment

1. Set secure `SECRET_KEY` in `.env`
2. Update `CORS_ORIGINS` to your frontend domain
3. Set `ALLOWED_HOSTS` appropriately
4. Use Supabase production project
5. Enable RLS (Row Level Security) in Supabase
6. Set up proper backup strategy

## Cost Estimation

### Free Tier (Development)
- Supabase: Free (500MB database, 1GB storage)
- Gemini: Free tier (60 req/min, 1500 req/day)
- **Total**: $0/month

### Production (1000 workflows/month)
- Supabase Pro: $25/month
- Gemini API: ~$15-30/month
- **Total**: ~$40-55/month

## Next Steps

1. Read [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed migration info
2. Check [README.md](./README.md) for API documentation
3. Review [RAG_IMPLEMENTATION.md](./RAG_IMPLEMENTATION.md) for RAG setup
4. See [WORKFLOW_IMPLEMENTATION.md](./WORKFLOW_IMPLEMENTATION.md) for workflow details

