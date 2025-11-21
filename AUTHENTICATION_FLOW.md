# Authentication Flow - NovaIntel

## Overview

NovaIntel uses **Supabase Authentication** with email verification. Users are automatically added to the `users` table after email verification and first login.

## Flow Diagram

```
1. User Registration
   ↓
2. Supabase Auth creates user (unverified)
   ↓
3. Email verification link sent
   ↓
4. User clicks link → Email verified
   ↓
5. User logs in
   ↓
6. Backend checks: email verified? ✓
   ↓
7. Backend checks: user exists in users table?
   ↓
8a. If NO → Create user in users table ✓
8b. If YES → Continue ✓
   ↓
9. User authenticated & can access app
```

## Step-by-Step Flow

### 1. Registration (`POST /auth/register`)

**What happens:**
- User submits registration form (email, password, full_name)
- Backend calls Supabase Auth `sign_up()`
- Supabase:
  - Creates user in `auth.users` table
  - Sends verification email
  - Returns user object (email_confirmed_at = null)

**Backend behavior:**
- ✅ Does NOT create user in `users` table yet
- ✅ Returns success message with email verification prompt
- ✅ Response includes `email_verified: false`

**Frontend behavior:**
- ✅ Shows message: "Check your email to verify your account"
- ✅ Redirects to login page
- ✅ Does NOT auto-login

### 2. Email Verification

**What happens:**
- User receives email from Supabase
- User clicks verification link
- Supabase verifies email:
  - Sets `email_confirmed_at` timestamp
  - Updates user status to verified

**Redirect:**
- User is redirected to `/verify-email` (or configured redirect URL)
- Frontend shows success message
- User can proceed to login

### 3. Login (`POST /auth/login`)

**What happens:**
- User submits login form (email, password)
- Backend calls Supabase Auth `sign_in_with_password()`

**Backend checks:**
1. ✅ **Email verified?** 
   - If NO → Return 403 error: "Please verify your email"
   - If YES → Continue

2. ✅ **User exists in `users` table?**
   - If NO → Create user in `users` table
   - If YES → Continue

3. ✅ **Return tokens:**
   - Access token (JWT)
   - Refresh token

**Frontend behavior:**
- ✅ Stores tokens in localStorage
- ✅ Redirects to dashboard
- ✅ Shows success message

### 4. API Requests (`get_current_user`)

**What happens:**
- Each authenticated API request calls `get_current_user()`
- Backend verifies JWT token with Supabase
- Backend checks if user exists in `users` table

**Backend checks:**
1. ✅ **Token valid?** 
   - If NO → Return 401 error
   - If YES → Continue

2. ✅ **Email verified?**
   - If NO → Return 403 error: "Please verify your email"
   - If YES → Continue

3. ✅ **User exists in `users` table?**
   - If NO → Create user (email is verified at this point)
   - If YES → Return user

## User Table Creation

Users are automatically added to the `users` table when:
1. ✅ Email is verified (`email_confirmed_at` is not null)
2. ✅ User logs in OR makes an authenticated API request
3. ✅ User doesn't exist in `users` table yet

**Created fields:**
- `email` - From Supabase Auth
- `full_name` - From user metadata or email
- `hashed_password` - Set to "supabase_auth" (not used)
- `is_active` - Set to `true`
- `role` - Default: "presales_manager"

## Error Handling

### Registration Errors
- ❌ **Email already registered** → 400 error
- ❌ **Invalid email format** → 400 error
- ❌ **Weak password** → 400 error

### Login Errors
- ❌ **Email not verified** → 403 error: "Please verify your email"
- ❌ **Incorrect password** → 401 error: "Incorrect email or password"
- ❌ **User not found** → 401 error

### API Request Errors
- ❌ **Invalid/expired token** → 401 error: Redirects to login
- ❌ **Email not verified** → 403 error: "Please verify your email"
- ❌ **User not in database** → 403 error (auto-creates if verified)

## Frontend Handling

### Registration Page
```typescript
// After successful registration
if (response.email_verified === false) {
  toast.success("Check your email to verify your account");
  navigate("/login");
}
```

### Login Page
```typescript
// Handle email verification error
if (error.message.includes("verify your email")) {
  toast.error("Please verify your email before logging in");
}
```

### Email Verification Page
- Shows success/error message
- Provides link to login
- Handles redirect from email link

## Supabase Configuration

### Required Settings

1. **Email Authentication**: Enabled
2. **Email Confirmations**: Enabled
3. **Redirect URL**: Set to your frontend URL (e.g., `http://localhost:8080/verify-email`)

### Email Template

Customize the "Confirm signup" template in:
- **Authentication** → **Email Templates** → **Confirm signup**

Default redirect URL: `{{ .ConfirmationURL }}`

## Testing the Flow

1. **Register new user:**
   ```bash
   POST /auth/register
   {
     "email": "test@example.com",
     "password": "test123456",
     "full_name": "Test User"
   }
   ```
   - ✅ Response: `email_verified: false`
   - ✅ Check Supabase Auth → Users (user created, not verified)
   - ✅ Check `users` table (user NOT created yet)

2. **Verify email:**
   - ✅ Check email inbox
   - ✅ Click verification link
   - ✅ Check Supabase Auth → Users (email_confirmed_at set)

3. **Login:**
   ```bash
   POST /auth/login
   {
     "email": "test@example.com",
     "password": "test123456"
   }
   ```
   - ✅ Response: Access token returned
   - ✅ Check `users` table (user created automatically)

4. **Access protected endpoint:**
   ```bash
   GET /projects/list
   Authorization: Bearer <token>
   ```
   - ✅ Response: Projects list (user already in database)

## Troubleshooting

### Issue: User created in Auth but not in users table

**Cause:** User hasn't logged in after verification yet.

**Solution:** User will be auto-created on first login.

### Issue: "Email not verified" error on login

**Cause:** User hasn't clicked verification link.

**Solution:** 
- Check email inbox
- Resend verification email if needed
- Check Supabase Auth → Users → email_confirmed_at

### Issue: User can't access API after login

**Cause:** User might not exist in `users` table.

**Solution:** Should auto-create on first API call, but check:
- Email is verified
- Database connection is working
- `users` table exists

### Issue: Verification email not received

**Solution:**
- Check spam folder
- Check Supabase Auth → Users → Resend confirmation email
- Verify SMTP settings in Supabase
- Check email templates are configured

## Security Notes

1. ✅ **Email verification required** - Users cannot access app without verification
2. ✅ **Automatic user creation** - Users added to database after verification
3. ✅ **Token validation** - All API requests validate JWT tokens
4. ✅ **Database sync** - Users table stays in sync with Supabase Auth

## Summary

- **Registration** → Supabase Auth (unverified)
- **Email Verification** → Supabase Auth (verified)
- **Login** → Creates user in `users` table (if verified)
- **API Requests** → Auto-creates user if needed (if verified)

This ensures users are only added to the `users` table after they've verified their email address.
