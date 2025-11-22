from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str = "pre_sales_analyst"  # Default to analyst, can be changed to pre_sales_manager

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str  # Supabase uses UUID strings
    email: str
    full_name: str
    is_active: bool = True
    email_verified: bool = False
    message: str = ""
    role: str = "pre_sales_analyst"  # Default role
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    company_name: str | None = None
    company_logo: str | None = None

class UserSettingsUpdate(BaseModel):
    proposal_tone: str | None = None
    ai_response_style: str | None = None
    secure_mode: bool | None = None
    auto_save_insights: bool | None = None
    theme_preference: str | None = None
    company_name: str | None = None
    company_logo: str | None = None

class UserSettingsResponse(BaseModel):
    proposal_tone: str
    ai_response_style: str
    secure_mode: bool
    auto_save_insights: bool
    theme_preference: str
    company_name: str | None = None
    company_logo: str | None = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

