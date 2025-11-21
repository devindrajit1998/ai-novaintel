# Supabase Setup Guide for NovaIntel

## Overview

NovaIntel uses Supabase for:
1. **Authentication** - User login/registration
2. **Database** - PostgreSQL database for all application data
3. **Storage** - File storage for RFP documents

## Step 1: Create Supabase Project

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in:
   - **Project Name**: novaintel (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose closest to your users
5. Click "Create new project"
6. Wait 2-3 minutes for project to initialize

## Step 2: Get API Keys

1. Go to **Settings** → **API** in your Supabase dashboard
2. Copy these values:

### Project URL
```
https://[your-project-ref].supabase.co
```
Copy this to `SUPABASE_URL` in your `.env` file

### API Keys
- **anon public** key → Copy to `SUPABASE_KEY`
- **service_role** key → Copy to `SUPABASE_SERVICE_KEY` (keep this secret!)

## Step 3: Setup Database

### Option A: Using SQL Migration (Recommended)

1. Go to **SQL Editor** in Supabase dashboard
2. Click "New query"
3. Copy and paste the contents of `supabase_migration.sql`
4. Click "Run" (or press Ctrl+Enter)
5. Verify tables were created:
   - Go to **Table Editor**
   - You should see: `users`, `projects`, `rfp_documents`, `insights`, `proposals`, `case_studies`

### Option B: Using SQLAlchemy (Auto-create)

If you have a valid `DATABASE_URL`, SQLAlchemy will auto-create tables on first run:

1. Get your database connection string:
   - Go to **Settings** → **Database**
   - Find "Connection string" → "URI"
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[project-ref].supabase.co:5432/postgres`
   - Copy to `DATABASE_URL` in `.env`

2. Start the backend - tables will be created automatically

## Step 4: Configure Email Authentication

1. Go to **Authentication** → **Settings** in Supabase dashboard
2. Enable **Email Authentication** (should be enabled by default)
3. Configure **Email Templates**:
   - Go to **Authentication** → **Email Templates**
   - Customize the **Confirm signup** template if needed
   - Set redirect URL to your frontend (e.g., `http://localhost:8080/verify-email`)

4. **Email Settings**:
   - **Enable email confirmations**: ON (recommended)
   - **Secure email change**: ON
   - **Disable email signups**: OFF

5. **SMTP Settings** (Optional - uses Supabase default SMTP by default):
   - If using custom SMTP, configure under **Settings** → **Auth** → **SMTP Settings**

## Step 5: Setup Storage Bucket

1. Go to **Storage** in Supabase dashboard
2. Click "New bucket"
3. Settings:
   - **Name**: `rfp-documents`
   - **Public bucket**: OFF (Private)
   - Click "Create bucket"

4. Configure RLS (Row Level Security):
   - Click on the bucket
   - Go to "Policies" tab
   - Add policy (if needed):
     ```sql
     -- Allow authenticated users to upload
     CREATE POLICY "Authenticated users can upload"
     ON storage.objects FOR INSERT
     TO authenticated
     WITH CHECK (bucket_id = 'rfp-documents');

     -- Allow users to read their own files
     CREATE POLICY "Users can read own files"
     ON storage.objects FOR SELECT
     TO authenticated
     USING (bucket_id = 'rfp-documents');
     ```

## Step 6: Configure Environment Variables

Create or update `backend/.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
SUPABASE_STORAGE_BUCKET=rfp-documents

# Database (optional - for direct PostgreSQL connection)
# Get from: Settings → Database → Connection string → URI
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Gemini API (for AI features)
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp

# CORS (frontend URL)
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

## Step 7: Verify Setup

### Test Backend Connection

Start the backend:
```bash
cd backend
python run.py
```

You should see:
```
✓ Supabase client initialized
✓ Supabase admin client initialized
✓ Database tables created/verified
✓ Gemini service ready: gemini-2.0-flash-exp
```

### Test Authentication Flow

1. **Register a new user:**
   - Open browser to `http://localhost:8000/docs`
   - Test `/auth/register` endpoint:
     ```json
     {
       "email": "test@example.com",
       "password": "test123456",
       "full_name": "Test User"
     }
     ```
   - Response should indicate email verification is required

2. **Check email:**
   - Check inbox for verification email from Supabase
   - Click the verification link in the email

3. **Login after verification:**
   - Test `/auth/login` endpoint:
     ```json
     {
       "email": "test@example.com",
       "password": "test123456"
     }
     ```
   - Should return access token successfully

4. **Verify user was created:**
   - Go to Supabase Dashboard → **Table Editor** → **users**
   - User should appear in the `users` table after first login

### Verify in Supabase

1. Go to **Authentication** → **Users**
2. You should see the registered user
3. Go to **Table Editor** → **users**
4. You should see a corresponding user record

## Database Schema Overview

### Tables

1. **users** - User accounts (linked to Supabase Auth)
2. **projects** - Presales projects
3. **rfp_documents** - Uploaded RFP files
4. **insights** - AI-generated insights
5. **proposals** - Proposal documents
6. **case_studies** - Success stories

### Relationships

```
users (1) ──< (many) projects
projects (1) ──< (many) rfp_documents
projects (1) ──< (1) insights
projects (1) ──< (many) proposals
```

### Row Level Security (RLS)

- Users can only access their own projects and related data
- Case studies are readable by all authenticated users
- Storage files are protected by bucket policies

## Troubleshooting

### Issue: "Supabase credentials not configured"
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are set in `.env`
- Restart the backend after changing `.env`

### Issue: "Authentication service not available"
- Verify Supabase project is active
- Check API keys are correct
- Ensure service is not paused (free tier pauses after inactivity)

### Issue: "Database connection failed"
- Verify `DATABASE_URL` is correct
- Check database password is correct
- Ensure connection string includes `[YOUR-PASSWORD]` placeholder replaced with actual password

### Issue: "Storage bucket not found"
- Verify bucket name matches `SUPABASE_STORAGE_BUCKET` in `.env`
- Check bucket exists in Storage dashboard
- Ensure bucket policies allow access

### Issue: 403 Forbidden on API calls
- User must be logged in (token in localStorage)
- Token might be expired - try logging in again
- Check RLS policies are configured correctly

## Security Notes

1. **Never commit** `.env` file to git
2. **Service role key** has admin access - keep it secret
3. **RLS policies** protect data at database level
4. **Storage bucket** should be private for production

## Next Steps

Once Supabase is configured:
1. ✅ Database tables created
2. ✅ Authentication working
3. ✅ Storage bucket ready
4. Run the frontend: `npm run dev`
5. Register a user and start creating projects!

## Support

- Supabase Docs: https://supabase.com/docs
- SQL Editor: https://app.supabase.com/project/_/sql
- API Docs: https://app.supabase.com/project/_/api
