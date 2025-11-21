# NovaIntel Setup Checklist

## ✅ Fixed Issues

1. **403 Forbidden Error** - Fixed API client to handle 403 errors properly
2. **Authentication Context** - Improved token decoding and user state management
3. **Supabase Integration** - Created comprehensive setup guide and migration script

## 📋 Setup Steps

### 1. Backend Setup

- [ ] Install Python dependencies: `cd backend && pip install -r requirements.txt`
- [ ] Configure Supabase:
  - [ ] Create Supabase project at https://app.supabase.com
  - [ ] Copy API keys from Settings → API
  - [ ] Create `.env` file in `backend/` directory
  - [ ] Add Supabase credentials to `.env`

- [ ] Setup Database:
  - [ ] Option A: Run `supabase_migration.sql` in Supabase SQL Editor
  - [ ] Option B: Configure `DATABASE_URL` for auto-creation
  
- [ ] Setup Storage:
  - [ ] Create `rfp-documents` bucket in Supabase Storage
  - [ ] Configure bucket policies if needed

- [ ] Configure Gemini API:
  - [ ] Get API key from https://aistudio.google.com/app/apikey
  - [ ] Add to `.env` as `GEMINI_API_KEY`

- [ ] Test backend:
  ```bash
  cd backend
  python run.py
  ```
  - [ ] Check console for: `✓ Supabase client ready`
  - [ ] Check console for: `✓ Database tables created/verified`
  - [ ] Test at http://localhost:8000/docs

### 2. Frontend Setup

- [ ] Install dependencies: `npm install`
- [ ] Configure API URL (optional):
  - [ ] Create `.env` file in root directory
  - [ ] Add: `VITE_API_BASE_URL=http://localhost:8000`
  
- [ ] Test frontend:
  ```bash
  npm run dev
  ```
  - [ ] Open http://localhost:8080
  - [ ] Verify frontend loads

### 3. First Use

- [ ] Register a new user at `/register`
  - [ ] Check Supabase Auth → Users (should see new user)
  - [ ] Check Supabase Table Editor → users (should see record)
  
- [ ] Login at `/login`
  - [ ] Verify redirects to `/dashboard`
  - [ ] Check browser localStorage for `access_token`
  
- [ ] Create a project:
  - [ ] Go to `/new-project`
  - [ ] Fill in client information
  - [ ] Upload an RFP file (PDF or DOCX)
  - [ ] Click "Analyze RFP"
  - [ ] Verify project appears in dashboard

- [ ] Test Insights:
  - [ ] View project insights at `/insights?project_id=X`
  - [ ] Test RAG chat functionality
  - [ ] Verify insights display correctly

## 🔧 Troubleshooting

### Issue: 403 Forbidden on API calls

**Solution:**
1. Ensure you're logged in (check localStorage for `access_token`)
2. If token exists but still 403:
   - Clear localStorage and login again
   - Check Supabase credentials in backend `.env`
   - Verify Supabase project is active (not paused)

### Issue: "Supabase credentials not configured"

**Solution:**
1. Check `backend/.env` file exists
2. Verify `SUPABASE_URL` and `SUPABASE_KEY` are set
3. Restart backend after changing `.env`

### Issue: "Database tables not created"

**Solution:**
1. Option A: Run `backend/supabase_migration.sql` in Supabase SQL Editor
2. Option B: Set `DATABASE_URL` in `.env` and restart backend
3. Check Supabase Table Editor to verify tables exist

### Issue: "Storage bucket not found"

**Solution:**
1. Go to Supabase Dashboard → Storage
2. Create bucket named `rfp-documents`
3. Ensure `SUPABASE_STORAGE_BUCKET=rfp-documents` in `.env`

### Issue: Authentication not working

**Solution:**
1. Verify Supabase Auth is enabled in project
2. Check API keys are correct (anon key for frontend, service key for backend)
3. Check CORS settings in backend `utils/config.py`
4. Verify token is being stored in localStorage after login

## 📁 File Structure

```
novaintel-ai/
├── backend/
│   ├── .env                    # Backend environment variables
│   ├── supabase_migration.sql  # Database schema
│   ├── SUPABASE_SETUP.md       # Detailed Supabase setup guide
│   └── ...
├── src/
│   ├── lib/
│   │   └── api.ts             # API client (fixed 403 handling)
│   ├── contexts/
│   │   └── AuthContext.tsx    # Auth context (improved)
│   └── ...
└── .env                        # Frontend environment variables (optional)
```

## 🔐 Environment Variables

### Backend `.env`

```env
# Supabase
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=rfp-documents

# Database (optional)
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Gemini
GEMINI_API_KEY=your-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# CORS
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

### Frontend `.env` (optional)

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📚 Documentation

- **Supabase Setup**: See `backend/SUPABASE_SETUP.md`
- **Database Schema**: See `backend/supabase_migration.sql`
- **API Documentation**: http://localhost:8000/docs (when backend is running)

## ✨ Next Steps

After setup is complete:
1. ✅ Test user registration and login
2. ✅ Create your first project
3. ✅ Upload and analyze an RFP
4. ✅ Review generated insights
5. ✅ Test RAG chat functionality
6. ✅ Build a proposal

## 🆘 Getting Help

1. Check backend console for error messages
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Check Supabase dashboard for database/storage issues
5. Review `backend/SUPABASE_SETUP.md` for detailed instructions
