"""
Email service for sending verification emails using Google SMTP.
"""
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from utils.config import settings

# Email configuration for Google SMTP
# Google SMTP settings: smtp.gmail.com, port 587, STARTTLS
# Lazy initialization - only create config when email is actually configured
_conf = None

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
    conf = get_email_config()
    if not conf:
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
    conf = get_email_config()
    if not conf:
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
    
    # Format proposal sections summary
    sections_summary = ""
    if proposal_sections and len(proposal_sections) > 0:
        sections_list = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for section in proposal_sections[:5]:  # Show first 5 sections
            section_title = section.get('title', 'Untitled Section') if isinstance(section, dict) else str(section)
            sections_list += f"<li style='margin: 5px 0;'>{section_title}</li>"
        if len(proposal_sections) > 5:
            sections_list += f"<li style='margin: 5px 0; color: #6b7280;'>... and {len(proposal_sections) - 5} more sections</li>"
        sections_list += "</ul>"
        sections_summary = f"<p style='margin: 5px 0;'><strong>Sections ({len(proposal_sections)}):</strong></p>{sections_list}"
    
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
                
                {f'<hr style="border: none; border-top: 1px solid #d1d5db; margin: 15px 0;"><h3 style="color: #1e40af;">Proposal Structure</h3>{sections_summary}' if sections_summary else ''}
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
        print(f"[OK] Proposal submission email sent to {manager_email}")
    except Exception as e:
        print(f"[WARNING] Failed to send proposal submission email to {manager_email}: {e}")

