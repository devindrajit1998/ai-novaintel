# NovaIntel Backend API

FastAPI backend for NovaIntel - AI-powered presales platform.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Set up database:**
   - Install PostgreSQL or use Supabase
   - Update `DATABASE_URL` in `.env`
   - Tables will be created automatically on first run

4. **Run the server:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token

### Projects
- `POST /projects/create` - Create a new project
- `GET /projects/list` - List all projects
- `GET /projects/{project_id}` - Get a specific project
- `PUT /projects/{project_id}` - Update a project
- `DELETE /projects/{project_id}` - Delete a project

### Upload
- `POST /upload/rfp` - Upload RFP document

### Insights
- `GET /insights/get?project_id={id}` - Get project insights

### Proposals
- `POST /proposal/save` - Save/create a proposal
- `GET /proposal/{proposal_id}` - Get a proposal
- `PUT /proposal/{proposal_id}` - Update a proposal
- `POST /proposal/export` - Export proposal as PDF/DOCX

### Case Studies
- `GET /case-studies` - List all case studies
- `POST /case-studies` - Create a case study
- `GET /case-studies/{id}` - Get a case study
- `PUT /case-studies/{id}` - Update a case study
- `DELETE /case-studies/{id}` - Delete a case study

## Project Structure

```
backend/
├── api/
│   ├── routers/      # API route handlers
│   └── schemas/       # Pydantic models for request/response
├── db/
│   └── database.py   # Database configuration
├── models/           # SQLAlchemy models
├── services/         # Business logic (to be implemented)
├── rag/              # RAG implementation (to be implemented)
├── agents/           # AI agents (to be implemented)
├── workflows/        # Workflow definitions (to be implemented)
├── utils/            # Utility functions
├── main.py           # FastAPI application entry point
└── requirements.txt  # Python dependencies
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Database Models

- **User**: User accounts with authentication
- **Project**: Presales projects
- **RFPDocument**: Uploaded RFP documents
- **Insights**: AI-generated insights
- **Proposal**: Proposal documents
- **CaseStudy**: Success stories and case studies

## Next Steps

1. Implement RAG pipeline for RFP analysis
2. Add AI agents for insights generation
3. Implement file text extraction (PDF/DOCX)
4. Add vector database integration
5. Implement proposal export functionality

