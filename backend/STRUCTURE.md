# Backend Structure

## Folder Organization

```
backend/
├── api/                    # API layer
│   ├── routers/           # Route handlers
│   │   ├── auth.py        # Authentication routes
│   │   ├── projects.py    # Project CRUD
│   │   ├── upload.py      # File upload
│   │   ├── insights.py    # Insights retrieval
│   │   ├── proposal.py    # Proposal management
│   │   └── case_studies.py # Case study CRUD
│   └── schemas/           # Pydantic models
│       ├── auth.py
│       ├── project.py
│       ├── insights.py
│       ├── proposal.py
│       └── case_study.py
│
├── db/                     # Database configuration
│   └── database.py        # SQLAlchemy setup
│
├── models/                # Database models (SQLAlchemy)
│   ├── user.py
│   ├── project.py
│   ├── rfp_document.py
│   ├── insights.py
│   ├── proposal.py
│   └── case_study.py
│
├── services/              # Business logic layer (placeholder)
├── rag/                   # RAG implementation (placeholder)
├── agents/                 # AI agents (placeholder)
├── workflows/              # Workflow definitions (placeholder)
│
├── utils/                 # Utility functions
│   ├── config.py          # Configuration management
│   ├── security.py        # JWT & password hashing
│   └── dependencies.py    # FastAPI dependencies
│
├── main.py                # FastAPI application entry point
├── run.py                 # Development server runner
├── requirements.txt       # Python dependencies
├── env.example            # Environment variables template
└── README.md              # Documentation
```

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

### Projects (`/projects`)
- `POST /projects/create` - Create project
- `GET /projects/list` - List all projects
- `GET /projects/{id}` - Get project
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project

### Upload (`/upload`)
- `POST /upload/rfp` - Upload RFP document

### Insights (`/insights`)
- `GET /insights/get?project_id={id}` - Get project insights

### Proposals (`/proposal`)
- `POST /proposal/save` - Save/create proposal
- `GET /proposal/{id}` - Get proposal
- `PUT /proposal/{id}` - Update proposal
- `POST /proposal/export` - Export proposal

### Case Studies (`/case-studies`)
- `GET /case-studies` - List case studies
- `POST /case-studies` - Create case study
- `GET /case-studies/{id}` - Get case study
- `PUT /case-studies/{id}` - Update case study
- `DELETE /case-studies/{id}` - Delete case study

## Database Models

1. **User** - User accounts with authentication
2. **Project** - Presales projects
3. **RFPDocument** - Uploaded RFP documents
4. **Insights** - AI-generated insights (JSON storage)
5. **Proposal** - Proposal documents with sections
6. **CaseStudy** - Success stories and case studies

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS middleware
- Trusted host middleware
- Token refresh mechanism

## Next Steps

1. Implement RAG pipeline for RFP analysis
2. Add AI agents for insights generation
3. Implement file text extraction (PDF/DOCX)
4. Add vector database integration (Pinecone/Supabase)
5. Implement proposal export functionality (PDF/DOCX generation)

