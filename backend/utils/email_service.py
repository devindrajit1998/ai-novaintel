"""
Email service for sending verification emails using Google SMTP.
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from utils.config import settings

# Email configuration for Google SMTP
# Google SMTP settings: smtp.gmail.com, port 587, STARTTLS
conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="NovaIntel",
    MAIL_STARTTLS=settings.MAIL_TLS,  # Use STARTTLS for Google SMTP
    MAIL_SSL_TLS=settings.MAIL_SSL,  # SSL not used for port 587
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_verification_email(email: str, verification_token: str):
    """Send email verification link via Google SMTP."""
    if not settings.mail_username or not settings.mail_password:
        print(f"⚠ Email not configured. Verification link: {settings.FRONTEND_URL}/verify-email/{verification_token}")
        return
    
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{verification_token}"
    
    message = MessageSchema(
        subject="Verify your NovaIntel account",
        recipients=[email],
        body=f"""
        <html>
        <body>
            <h2>Welcome to NovaIntel!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>Or copy this link: {verification_url}</p>
            <p>This link will expire in 7 days.</p>
        </body>
        </html>
        """,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset link via Google SMTP."""
    if not settings.mail_username or not settings.mail_password:
        print(f"⚠ Email not configured. Reset link: {settings.FRONTEND_URL}/reset-password?token={reset_token}")
        return
    
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    message = MessageSchema(
        subject="Reset your NovaIntel password",
        recipients=[email],
        body=f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>Or copy this link: {reset_url}</p>
            <p>This link will expire in 7 days.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_proposal_submission_email(
    manager_email: str,
    manager_name: str,
    proposal_title: str,
    submitter_name: str,
    submitter_message: str = None,
    proposal_id: int = None,
    project_id: int = None
):
    """Send email notification to manager when a proposal is submitted for approval."""
    if not settings.mail_username or not settings.mail_password:
        print(f"⚠ Email not configured. Proposal submission notification for: {manager_email}")
        print(f"   Proposal: {proposal_title} by {submitter_name}")
        return
    
    login_url = f"{settings.FRONTEND_URL}/login"
    admin_dashboard_url = f"{settings.FRONTEND_URL}/admin"
    
    message_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">New Proposal Submitted for Review</h2>
            
            <p>Hello {manager_name},</p>
            
            <p>A new proposal has been submitted and requires your review:</p>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Proposal Title:</strong> {proposal_title}</p>
                <p style="margin: 5px 0;"><strong>Submitted By:</strong> {submitter_name}</p>
                {f'<p style="margin: 5px 0;"><strong>Message:</strong> {submitter_message}</p>' if submitter_message else ''}
            </div>
            
            <p>Please review the proposal and provide your feedback.</p>
            
            <div style="margin: 30px 0; text-align: center;">
                <a href="{admin_dashboard_url}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; 
                          font-weight: bold;">
                    Review Proposal
                </a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Or <a href="{login_url}" style="color: #2563eb;">login to your account</a> to access the admin dashboard.
            </p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            
            <p style="color: #6b7280; font-size: 12px;">
                This is an automated notification from NovaIntel. 
                Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"New Proposal Submitted: {proposal_title}",
        recipients=[manager_email],
        body=message_body,
        subtype="html"
    )
    
    try:
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"[OK] Proposal submission email sent to {manager_email}")
    except Exception as e:
        print(f"[WARNING] Failed to send proposal submission email to {manager_email}: {e}")

