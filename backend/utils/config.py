from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database - Direct PostgreSQL
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/novaintel"
    
    # Vector Database - Chroma
    VECTOR_DB_TYPE: str = "chroma"  # "chroma" or "qdrant" or "pgvector"
    CHROMA_PERSIST_DIR: str = "./chroma_db"  # Local Chroma storage
    # OR for Qdrant:
    # QDRANT_URL: str = "http://localhost:6333"
    # QDRANT_API_KEY: str = ""
    
    # LLM Provider - Gemini
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"  # "gemini" or "openai"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # Legacy OpenAI (optional fallback)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # File Upload - Local Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS: str = ".pdf,.docx"  # Comma-separated string in .env
    
    # Email Configuration (for email verification)
    # Support both SMTP_* and MAIL_* naming (fastapi-mail uses MAIL_*)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    FRONTEND_URL: str = "http://localhost:8080"  # For email verification links
    
    # MAIL_* variables (for fastapi-mail compatibility - from .env)
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    
    @property
    def mail_server(self) -> str:
        """Get mail server from MAIL_SERVER or SMTP_HOST."""
        return self.MAIL_SERVER or self.SMTP_HOST
    
    @property
    def mail_port(self) -> int:
        """Get mail port from MAIL_PORT or SMTP_PORT."""
        if self.MAIL_SERVER:  # If MAIL_SERVER is set, prefer MAIL_PORT
            return self.MAIL_PORT
        return self.SMTP_PORT
    
    @property
    def mail_username(self) -> str:
        """Get mail username from MAIL_USERNAME or SMTP_USER."""
        return self.MAIL_USERNAME or self.SMTP_USER
    
    @property
    def mail_password(self) -> str:
        """Get mail password from MAIL_PASSWORD or SMTP_PASSWORD."""
        return self.MAIL_PASSWORD or self.SMTP_PASSWORD
    
    @property
    def mail_from(self) -> str:
        """Get mail from email from MAIL_FROM or SMTP_FROM_EMAIL."""
        return self.MAIL_FROM or self.SMTP_FROM_EMAIL
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions from comma-separated string."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]
    
    # CORS (comma-separated string in .env, or list in code)
    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:5173,http://127.0.0.1:8080"
    ALLOWED_HOSTS: str = "*"  # Comma-separated string in .env
    
    # Database Pool Controls (PgBouncer-friendly)
    DB_POOL_SIZE: int = 5               # keep low to avoid hitting PgBouncer pool
    DB_MAX_OVERFLOW: int = 0            # avoid burst connections
    DB_POOL_TIMEOUT: int = 30           # seconds to wait for a pool connection
    DB_POOL_RECYCLE: int = 1800         # recycle connections every 30 min
    DB_USE_NULLPOOL: bool = False       # set true to delegate pooling to PgBouncer
    DB_CONNECT_TIMEOUT: int = 5         # seconds for TCP connect timeout
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse allowed hosts from comma-separated string."""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        if isinstance(self.ALLOWED_HOSTS, list):
            return self.ALLOWED_HOSTS
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env that aren't defined

settings = Settings()

