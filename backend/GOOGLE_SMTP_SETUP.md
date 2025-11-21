# Google SMTP Setup Guide

## Overview

The email service is configured to use Google SMTP (Gmail) for sending verification emails.

## Prerequisites

1. A Gmail account
2. App Password (not your regular Gmail password)

## Step 1: Generate Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already enabled)
3. Scroll down to **App passwords**
4. Select **Mail** and **Other (Custom name)**
5. Enter "NovaIntel" as the app name
6. Click **Generate**
7. Copy the 16-character app password (you'll use this in `.env`)

## Step 2: Configure .env File

Add these variables to your `backend/.env` file:

```env
# Google SMTP Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_FROM=your-email@gmail.com
MAIL_TLS=True
MAIL_SSL=False

# Frontend URL (for verification links)
FRONTEND_URL=http://localhost:8080
```

### Example:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=myemail@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop
MAIL_FROM=myemail@gmail.com
MAIL_TLS=True
MAIL_SSL=False
FRONTEND_URL=http://localhost:8080
```

**Important Notes:**
- Use your **App Password**, not your regular Gmail password
- Remove spaces from the app password (if any)
- `MAIL_USERNAME` and `MAIL_FROM` should be the same Gmail address
- `MAIL_TLS=True` enables STARTTLS (required for port 587)
- `MAIL_SSL=False` (SSL is not used with port 587)

## Step 3: Test Email Configuration

After setting up, restart your backend server:

```bash
cd backend
python run.py
```

When a user registers, the verification email will be sent automatically.

## Troubleshooting

### "Authentication failed" error

- Verify you're using an **App Password**, not your regular password
- Ensure 2-Step Verification is enabled on your Google account
- Check that the app password is correct (no spaces)

### "Connection refused" error

- Check your firewall/antivirus isn't blocking port 587
- Verify `MAIL_SERVER=smtp.gmail.com` is correct
- Ensure `MAIL_PORT=587` is set

### Email not sending

- Check backend console for error messages
- Verify all MAIL_* variables are set correctly
- Test with a simple email client first to verify credentials

### "Less secure app access" error

- This shouldn't happen with App Passwords
- If it does, ensure you're using App Password, not regular password

## Alternative: Using SMTP_* Variables

You can also use `SMTP_*` variables instead of `MAIL_*`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

The system will automatically map these to the email service.

## Security Notes

- Never commit your `.env` file to version control
- App Passwords are safer than regular passwords
- Each app should have its own App Password
- Revoke App Passwords if compromised

## Production Setup

For production:
- Use environment variables instead of `.env` file
- Consider using a dedicated email service (SendGrid, AWS SES, etc.)
- Update `FRONTEND_URL` to your production domain
- Use proper email templates

