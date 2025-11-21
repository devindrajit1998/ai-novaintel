# Setup Status

## ✅ Completed

1. **Backend Dependencies** - All Python packages installed
2. **Frontend Dependencies** - All npm packages installed  
3. **Configuration Files** - Created setup guides
4. **Servers Started** - Backend and frontend servers are running

## ⚠️ Action Required

### 1. Create Backend .env File

**CRITICAL**: You must manually create `backend/.env` file before the backend will work properly.

Copy the content from `QUICK_START.md` or use this template:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/novaintel
SECRET_KEY=cd572dac2913af842bd63f04dd16d04f8c56b036eb1e8ec6064cbe7a3d7ed537
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx
FRONTEND_URL=http://localhost:8080
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

**Get Gemini API Key**: https://aistudio.google.com/app/apikey

### 2. Setup PostgreSQL Database

1. Install PostgreSQL if not already installed
2. Create the database:
   ```sql
   CREATE DATABASE novaintel;
   ```
3. Run the migration:
   ```bash
   psql -d novaintel -f backend/db/migration.sql
   ```

Or use pgAdmin or any PostgreSQL client to run the SQL from `backend/db/migration.sql`

### 3. Update DATABASE_URL

In `backend/.env`, update the `DATABASE_URL` with your actual PostgreSQL credentials:
- Replace `postgres` with your PostgreSQL username
- Replace `postgres` (password) with your PostgreSQL password
- Update `localhost:5432` if your PostgreSQL is on a different host/port

## 🚀 Current Status

- **Backend Server**: Starting on http://localhost:8000
- **Frontend Server**: Starting on http://localhost:8080

## 📝 Next Steps

1. Create `backend/.env` file (see above)
2. Setup PostgreSQL database
3. Add your Gemini API key to `.env`
4. Restart backend server if needed
5. Visit http://localhost:8080 to access the application

## 🔍 Verify Setup

### Check Backend
```bash
curl http://localhost:8000/health
```
Should return: `{"status":"healthy"}`

### Check Frontend
Open browser: http://localhost:8080

### Check API Docs
Open browser: http://localhost:8000/docs

## ⚡ Quick Commands

**Start Backend** (Terminal 1):
```bash
cd backend
python run.py
```

**Start Frontend** (Terminal 2):
```bash
npm run dev
```

## 🆘 Troubleshooting

### Backend won't start
- Check if `.env` file exists in `backend/` directory
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Look for error messages in console

### Database connection errors
- Verify PostgreSQL is installed and running
- Check database credentials in `DATABASE_URL`
- Ensure database `novaintel` exists
- Run migration SQL if tables don't exist

### Frontend can't connect
- Ensure backend is running on port 8000
- Check CORS settings in backend `.env`
- Verify `VITE_API_BASE_URL` if set in frontend `.env`

