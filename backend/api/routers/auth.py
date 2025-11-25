from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import sys
from db.database import get_db
from models.user import User
from api.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshTokenRequest, UserResponse, UserUpdate, UserSettingsUpdate, UserSettingsResponse, ForgotPasswordRequest, ResetPasswordRequest
from utils.config import settings
from utils.dependencies import get_current_user
from utils.websocket_manager import global_ws_manager
from utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_email_verification_token,
    verify_email_token,
    validate_password_strength
)
from utils.email_service import send_verification_email

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user with email verification.
    """
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate role
        ALLOWED_ROLES = ["pre_sales_analyst", "pre_sales_manager"]
        user_role = getattr(user_data, 'role', "pre_sales_analyst")
        if user_role not in ALLOWED_ROLES:
            user_role = "pre_sales_analyst"  # Default to analyst if invalid role
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        verification_token = create_email_verification_token(user_data.email)
        
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_role,
            is_active=False,  # Inactive until email verified
            email_verified=False,
            email_verification_token=verification_token
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Send verification email
        try:
            await send_verification_email(user_data.email, verification_token)
            print(f"[REGISTRATION] Verification email sent successfully to: {user_data.email}", file=sys.stderr, flush=True)
        except Exception as e:
            # Error already logged in email_service with full details
            print(f"[REGISTRATION WARNING] User registered but verification email failed. User ID: {new_user.id}, Email: {user_data.email}", file=sys.stderr, flush=True)
            # Continue anyway - user can request resend
        
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "is_active": new_user.is_active,
            "email_verified": new_user.email_verified,
            "message": "Registration successful. Please check your email to verify your account."
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token.
    User must have verified their email.
    """
    import sys
    import traceback
    
    try:
        print(f"\n🔐 LOGIN ATTEMPT: {credentials.email}", file=sys.stderr, flush=True)
        
        # Find user
        user = db.query(User).filter(User.email == credentials.email).first()
        
        if not user:
            print(f"❌ LOGIN FAILED: User not found for email: {credentials.email}", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        print(f"✓ User found: {user.email} (ID: {user.id})", file=sys.stderr, flush=True)
        print(f"  Email verified: {user.email_verified}, Active: {user.is_active}", file=sys.stderr, flush=True)
        print(f"  Password hash prefix: {user.hashed_password[:20] if user.hashed_password else 'None'}...", file=sys.stderr, flush=True)
        
        # Verify password
        try:
            password_valid = verify_password(credentials.password, user.hashed_password)
            print(f"  Password verification: {'✓ Valid' if password_valid else '❌ Invalid'}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"❌ Password verification error: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not password_valid:
            print(f"❌ LOGIN FAILED: Password verification failed for: {credentials.email}", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if email is verified
        if not user.email_verified:
            print(f"❌ LOGIN FAILED: Email not verified for: {credentials.email}", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in. Check your inbox for the verification link."
            )
        
        # Activate user if not already active
        if not user.is_active:
            user.is_active = True
            db.commit()
        
        # Create tokens (include role for frontend access)
        try:
            access_token = create_access_token(data={
                "sub": user.email, 
                "email": user.email, 
                "user_id": user.id,
                "role": user.role or "pre_sales_analyst"
            })
            refresh_token = create_refresh_token(data={
                "sub": user.email, 
                "email": user.email, 
                "user_id": user.id,
                "role": user.role or "pre_sales_analyst"
            })
        except Exception as e:
            print(f"❌ Token creation error: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication tokens"
            )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status codes)
        raise
    except Exception as e:
        # Catch any other unexpected errors
        print(f"❌ UNEXPECTED LOGIN ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    # Decode refresh token
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_email = payload.get("sub") or payload.get("email")
    user = db.query(User).filter(User.email == user_email).first()
    
    if not user or not user.is_active or not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens (include role)
    access_token = create_access_token(data={
        "sub": user.email, 
        "email": user.email, 
        "user_id": user.id,
        "role": user.role or "pre_sales_analyst"
    })
    refresh_token = create_refresh_token(data={
        "sub": user.email, 
        "email": user.email, 
        "user_id": user.id,
        "role": user.role or "pre_sales_analyst"
    })
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify user email using verification token."""
    import sys
    
    print(f"\n{'='*60}", file=sys.stderr, flush=True)
    print(f"[EMAIL VERIFICATION] Request received", file=sys.stderr, flush=True)
    print(f"Token (first 20 chars): {token[:20]}...", file=sys.stderr, flush=True)
    
    try:
        email = verify_email_token(token)
        
        if not email:
            print(f"[EMAIL VERIFICATION] Token validation failed: Invalid or expired token", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        print(f"[EMAIL VERIFICATION] Token validated. Email: {email}", file=sys.stderr, flush=True)
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"[EMAIL VERIFICATION] User not found for email: {email}", file=sys.stderr, flush=True)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        print(f"[EMAIL VERIFICATION] User found: ID={user.id}, Email={user.email}, Already verified={user.email_verified}", file=sys.stderr, flush=True)
        
        if user.email_verified:
            print(f"[EMAIL VERIFICATION] Email already verified for: {email}", file=sys.stderr, flush=True)
            print(f"{'='*60}\n", file=sys.stderr, flush=True)
            return {"message": "Email already verified"}
        
        # Verify email
        user.email_verified = True
        user.is_active = True
        from utils.timezone import now_utc_from_ist
        user.email_verified_at = now_utc_from_ist()
        user.email_verification_token = None
        db.commit()
        db.refresh(user)
        
        print(f"[EMAIL VERIFICATION] SUCCESS - Email verified for: {email}", file=sys.stderr, flush=True)
        print(f"  User ID: {user.id}", file=sys.stderr, flush=True)
        print(f"  Email verified: {user.email_verified}", file=sys.stderr, flush=True)
        print(f"  User active: {user.is_active}", file=sys.stderr, flush=True)
        print(f"  Verified at: {user.email_verified_at}", file=sys.stderr, flush=True)
        print(f"{'='*60}\n", file=sys.stderr, flush=True)
        
        return {"message": "Email verified successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[EMAIL VERIFICATION] ERROR: {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )

@router.get("/managers", response_model=List[UserResponse])
async def get_managers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all pre-sales managers. Available to all authenticated users."""
    MANAGER_ROLE = "pre_sales_manager"
    managers = db.query(User).filter(
        User.role == MANAGER_ROLE,
        User.is_active == True,
        User.email_verified == True
    ).all()
    
    return [
        {
            "id": str(manager.id),
            "email": manager.email,
            "full_name": manager.full_name,
            "is_active": manager.is_active,
            "email_verified": manager.email_verified,
            "role": manager.role
        }
        for manager in managers
    ]

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "email_verified": current_user.email_verified,
        "role": current_user.role or "presales_manager"
    }

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.role is not None:
        current_user.role = user_update.role
    
    from utils.timezone import now_utc_from_ist
    current_user.updated_at = now_utc_from_ist()
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "email_verified": current_user.email_verified,
        "role": current_user.role or "presales_manager"
    }

@router.get("/me/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user settings from database."""
    return {
        "proposal_tone": current_user.proposal_tone or "professional",
        "ai_response_style": current_user.ai_response_style or "balanced",
        "secure_mode": current_user.secure_mode if current_user.secure_mode is not None else False,
        "auto_save_insights": current_user.auto_save_insights if current_user.auto_save_insights is not None else True,
        "theme_preference": current_user.theme_preference or "light",
        "company_name": current_user.company_name,
        "company_logo": current_user.company_logo
    }

@router.put("/me/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings in database."""
    update_data = settings_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "proposal_tone": current_user.proposal_tone or "professional",
        "ai_response_style": current_user.ai_response_style or "balanced",
        "secure_mode": current_user.secure_mode if current_user.secure_mode is not None else False,
        "auto_save_insights": current_user.auto_save_insights if current_user.auto_save_insights is not None else True,
        "theme_preference": current_user.theme_preference or "light",
        "company_name": current_user.company_name,
        "company_logo": current_user.company_logo
    }

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send password reset email."""
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Create password reset token
    from utils.security import create_email_verification_token
    reset_token = create_email_verification_token(user.email)
    
    # Store token in user record
    user.email_verification_token = reset_token
    db.commit()
    
    # Send reset email
    try:
        from utils.email_service import send_password_reset_email
        await send_password_reset_email(user.email, reset_token)
        print(f"[PASSWORD RESET] Password reset email sent successfully to: {user.email}", file=sys.stderr, flush=True)
    except Exception as e:
        # Error already logged in email_service with full details
        print(f"[PASSWORD RESET WARNING] Password reset token created but email failed. Email: {user.email}", file=sys.stderr, flush=True)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using token."""
    from utils.security import verify_email_token, get_password_hash
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Verify token
    email = verify_email_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.email_verification_token = None  # Clear the token
    db.commit()
    
    return {"message": "Password reset successfully"}

# Admin endpoints
@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all users. Only accessible to managers."""
    MANAGER_ROLE = "pre_sales_manager"
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    users = db.query(User).all()
    
    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "email_verified": user.email_verified,
            "role": user.role or "pre_sales_analyst"
        }
        for user in users
    ]

@router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user (role, active status). Only accessible to managers."""
    MANAGER_ROLE = "pre_sales_manager"
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        user.role = user_update.role
    
    from utils.timezone import now_utc_from_ist
    user.updated_at = now_utc_from_ist()
    db.commit()
    db.refresh(user)
    
    # Broadcast user update via WebSocket
    try:
        await global_ws_manager.broadcast({
            "type": "user_updated",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role or "pre_sales_analyst",
                "is_active": user.is_active
            }
        }, subscription_type="users")
    except Exception as e:
        print(f"Error broadcasting user update: {e}")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "role": user.role or "pre_sales_analyst"
    }

@router.put("/admin/users/{user_id}/activate", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate or deactivate a user. Only accessible to managers."""
    MANAGER_ROLE = "pre_sales_manager"
    if current_user.role != MANAGER_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager role required."
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    from utils.timezone import now_utc_from_ist
    user.updated_at = now_utc_from_ist()
    db.commit()
    db.refresh(user)
    
    # Broadcast user status change via WebSocket
    try:
        await global_ws_manager.broadcast({
            "type": "user_status_changed",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "role": user.role or "pre_sales_analyst"
            }
        }, subscription_type="users")
    except Exception as e:
        print(f"Error broadcasting user status change: {e}")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "role": user.role or "pre_sales_analyst"
    }