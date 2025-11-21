from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
import sys
import warnings
import logging

# Suppress langchain warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*langchain.*", category=DeprecationWarning)

from api.routers import (
    auth, projects, upload, insights, proposal,
    case_studies, rag, agents, case_study_documents,
    search, notifications
)
from db.database import engine, Base
from utils.config import settings

# Import models so SQLAlchemy registers them
from models import (
    User, Project, RFPDocument, Insights,
    Proposal, CaseStudy, Notification
)

try:
    from models.case_study_document import CaseStudyDocument
except ImportError:
    pass

# Request logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response


# Lifespan events: database init + services init
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created/verified")

        from db.migrate_user_settings import migrate_user_settings
        from db.migrate_notifications import migrate_notifications
        from db.migrate_case_studies import migrate_case_studies
        from db.migrate_proposals_table import migrate_proposals_table

        migrate_user_settings()
        migrate_notifications()
        migrate_case_studies()
        migrate_proposals_table()

    except Exception as e:
        print(f"[WARNING] Database initialization warning: {e}")

    # Service check logs
    try:
        from utils.gemini_service import gemini_service
        if gemini_service.is_available():
            print(f"[OK] Gemini ready: {settings.GEMINI_MODEL}")
        else:
            print("[WARNING] Gemini service not available - check GEMINI_API_KEY in .env")
    except Exception as e:
        print(f"[WARNING] Gemini service failed: {e}")

    try:
        from rag.vector_store import vector_store_manager
        from rag.embedding_service import embedding_service
        
        if vector_store_manager.is_available():
            print(f"[OK] Vector store ready: {settings.VECTOR_DB_TYPE}")
        else:
            print("[ERROR] Vector store NOT available - check logs above for details")
            
        if embedding_service.is_available():
            print("[OK] Embedding service ready")
        else:
            print("[ERROR] Embedding service NOT available - check logs above for details")
    except Exception as e:
        print(f"[WARNING] RAG services failed: {e}")

    yield


app = FastAPI(
    title="NovaIntel API",
    description="AI-powered presales platform backend API",
    version="1.0.0",
    lifespan=lifespan
)

# -----------------------------------------------------
# ✅ CORS MIDDLEWARE — MUST COME FIRST
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # or settings.cors_origins_list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Security: Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts_list
)

# Logging middleware
app.add_middleware(LoggingMiddleware)


# -----------------------------------------------------
# VALIDATION ERROR HANDLER
# -----------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(x) for x in e["loc"] if x != "body"),
            "message": e["msg"],
            "type": e["type"],
        }
        for e in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


# -----------------------------------------------------
# UNHANDLED EXCEPTIONS (500)
# -----------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logging.error(f"Unhandled Exception: {str(exc)}", exc_info=True)

    # CORS headers will still be injected by middleware
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc)
        }
    )




# -----------------------------------------------------
# ROUTERS
# -----------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/projects", tags=["Projects"])
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])
app.include_router(proposal.router, prefix="/proposal", tags=["Proposal"])
app.include_router(case_studies.router, prefix="/case-studies", tags=["Case Studies"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(agents.router, prefix="/agents", tags=["Multi-Agent Workflow"])
app.include_router(case_study_documents.router, prefix="/case-study-documents", tags=["Case Study Documents"])
app.include_router(search.router, tags=["Search"])
app.include_router(notifications.router, tags=["Notifications"])


@app.get("/")
async def root():
    return {
        "message": "NovaIntel API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
