"""
Email service for sending verification emails using Google SMTP.
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from utils.config import settings
from datetime import datetime
import traceback
import sys

# Email configuration for Google SMTP
# Google SMTP settings: smtp.gmail.com, port 587, STARTTLS
# Lazy initialization - only create config when email is actually configured
_conf = None

def _log_email_error(email_type: str, recipient: str, error: Exception, context: str = ""):
    """Log email sending errors with full details."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    error_msg = str(error)
    
    print(f"\n{'='*60}", file=sys.stderr, flush=True)
    print(f"[EMAIL ERROR] {timestamp}", file=sys.stderr, flush=True)
    print(f"{'='*60}", file=sys.stderr, flush=True)
    print(f"Email Type: {email_type}", file=sys.stderr, flush=True)
    print(f"Recipient: {recipient}", file=sys.stderr, flush=True)
    if context:
        print(f"Context: {context}", file=sys.stderr, flush=True)
    print(f"Error Type: {error_type}", file=sys.stderr, flush=True)
    print(f"Error Message: {error_msg}", file=sys.stderr, flush=True)
    print(f"\nFull Traceback:", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr, flush=True)

def get_email_config():
    """Get or create email configuration. Returns None if email is not configured."""
    global _conf
    if _conf is None and settings.mail_from and settings.mail_username and settings.mail_password:
        _conf = ConnectionConfig(
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
    return _conf

async def send_verification_email(email: str, verification_token: str):
    """Send email verification link via Google SMTP."""
    try:
        conf = get_email_config()
        if not conf:
            print(f"[EMAIL WARNING] Email service not configured. Cannot send verification email to: {email}", file=sys.stderr, flush=True)
            print(f"Verification link (manual): {settings.FRONTEND_URL}/verify-email?token={verification_token}", file=sys.stderr, flush=True)
            return
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
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
        print(f"[EMAIL SUCCESS] Verification email sent to: {email}", file=sys.stderr, flush=True)
    except Exception as e:
        _log_email_error("Verification Email", email, e, "User Registration")
        raise

async def send_password_reset_email(email: str, reset_token: str):
    """Send password reset link via Google SMTP."""
    try:
        conf = get_email_config()
        if not conf:
            print(f"[EMAIL WARNING] Email service not configured. Cannot send password reset email to: {email}", file=sys.stderr, flush=True)
            print(f"Reset link (manual): {settings.FRONTEND_URL}/reset-password?token={reset_token}", file=sys.stderr, flush=True)
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
        print(f"[EMAIL SUCCESS] Password reset email sent to: {email}", file=sys.stderr, flush=True)
    except Exception as e:
        _log_email_error("Password Reset Email", email, e, "Password Reset Request")
        raise

async def send_proposal_submission_email(
    manager_email: str,
    manager_name: str,
    proposal_title: str,
    submitter_name: str,
    submitter_message: str = None,
    proposal_id: int = None,
    project_id: int = None,
    project_name: str = None,
    client_name: str = None,
    industry: str = None,
    region: str = None,
    proposal_sections: list = None,
    template_type: str = None,
    submitted_at: str = None
):
    """Send email notification to admin/manager when a proposal is submitted for approval."""
    conf = get_email_config()
    if not conf:
        print(f"⚠ Email not configured. Proposal submission notification for: {manager_email}")
        print(f"   Proposal: {proposal_title} by {submitter_name}")
        return
    
    login_url = f"{settings.FRONTEND_URL}/login"
    admin_dashboard_url = f"{settings.FRONTEND_URL}/admin/proposals"
    proposal_url = f"{settings.FRONTEND_URL}/admin/proposals" if proposal_id else admin_dashboard_url
    
    # Format proposal sections preview
    sections_preview = ""
    if proposal_sections and len(proposal_sections) > 0:
        sections_preview = "<div style='margin: 20px 0;'>"
        sections_preview += f"<h3 style='color: #1e40af; margin-bottom: 15px;'>Proposal Preview ({len(proposal_sections)} sections)</h3>"
        
        for idx, section in enumerate(proposal_sections[:10]):  # Show first 10 sections
            section_title = section.get('title', f'Section {idx + 1}') if isinstance(section, dict) else f'Section {idx + 1}'
            section_content = section.get('content', '') if isinstance(section, dict) else ''
            
            # Truncate content for email preview (first 500 chars)
            content_preview = section_content[:500] if section_content else "No content available"
            if len(section_content) > 500:
                content_preview += "..."
            
            # Escape HTML and convert markdown-like formatting to HTML for email
            import html
            content_html = html.escape(content_preview)
            # Convert markdown to HTML
            # Handle bold **text**
            import re
            content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content_html)
            # Handle italic *text* (but not **text**)
            content_html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', content_html)
            # Handle line breaks
            content_html = content_html.replace('\n\n', '</p><p style="margin: 8px 0;">')
            content_html = content_html.replace('\n', '<br>')
            
            sections_preview += f"""
            <div style='background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 15px; margin-bottom: 15px;'>
                <h4 style='color: #1e40af; margin: 0 0 10px 0; font-size: 16px; font-weight: 600;'>{section_title}</h4>
                <div style='color: #374151; font-size: 14px; line-height: 1.6;'>
                    <p style="margin: 8px 0;">{content_html}</p>
                </div>
            </div>
            """
        
        if len(proposal_sections) > 10:
            sections_preview += f"<p style='color: #6b7280; font-size: 14px; margin-top: 10px;'>... and {len(proposal_sections) - 10} more sections (view full proposal in dashboard)</p>"
        
        sections_preview += "</div>"
    
    # Format submitted date
    submitted_date = submitted_at if submitted_at else "Just now"
    
    message_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">New Proposal Submitted for Review</h2>
            
            <p>Hello {manager_name},</p>
            
            <p>A new proposal has been submitted and requires your review:</p>
            
            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                <h3 style="margin-top: 0; color: #1e40af;">Proposal Details</h3>
                <p style="margin: 8px 0;"><strong>Proposal Title:</strong> {proposal_title}</p>
                <p style="margin: 8px 0;"><strong>Proposal ID:</strong> #{proposal_id if proposal_id else 'N/A'}</p>
                <p style="margin: 8px 0;"><strong>Template Type:</strong> {template_type.title() if template_type else 'Full'}</p>
                <p style="margin: 8px 0;"><strong>Submitted At:</strong> {submitted_date}</p>
                
                <hr style="border: none; border-top: 1px solid #d1d5db; margin: 15px 0;">
                
                <h3 style="color: #1e40af;">Project Information</h3>
                <p style="margin: 8px 0;"><strong>Project:</strong> {project_name if project_name else 'N/A'}</p>
                <p style="margin: 8px 0;"><strong>Client:</strong> {client_name if client_name else 'N/A'}</p>
                <p style="margin: 8px 0;"><strong>Industry:</strong> {industry if industry else 'N/A'}</p>
                <p style="margin: 8px 0;"><strong>Region:</strong> {region if region else 'N/A'}</p>
                <p style="margin: 8px 0;"><strong>Project ID:</strong> #{project_id if project_id else 'N/A'}</p>
                
                <hr style="border: none; border-top: 1px solid #d1d5db; margin: 15px 0;">
                
                <h3 style="color: #1e40af;">Submitter Information</h3>
                <p style="margin: 8px 0;"><strong>Submitted By:</strong> {submitter_name}</p>
                {f'<p style="margin: 8px 0;"><strong>Message from Submitter:</strong></p><p style="margin: 8px 0; padding: 10px; background-color: #ffffff; border-radius: 4px; font-style: italic;">{submitter_message}</p>' if submitter_message else ''}
                
                {f'<hr style="border: none; border-top: 1px solid #d1d5db; margin: 15px 0;">{sections_preview}' if sections_preview else ''}
            </div>
            
            <p style="font-size: 16px; font-weight: 500;">Please review the proposal and provide your feedback.</p>
            
            <div style="margin: 30px 0; text-align: center;">
                <a href="{admin_dashboard_url}" 
                   style="background-color: #2563eb; color: white; padding: 14px 28px; 
                          text-decoration: none; border-radius: 6px; display: inline-block; 
                          font-weight: bold; font-size: 16px;">
                    Review Proposal Now
                </a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                Or <a href="{login_url}" style="color: #2563eb; text-decoration: underline;">login to your account</a> to access the admin dashboard.
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
        print(f"[EMAIL SUCCESS] Proposal submission email sent to: {manager_email} (Proposal: {proposal_title})", file=sys.stderr, flush=True)
    except Exception as e:
        _log_email_error(
            "Proposal Submission Email", 
            manager_email, 
            e, 
            f"Proposal: {proposal_title}, Submitter: {submitter_name}, Proposal ID: {proposal_id}"
        )
        raise

