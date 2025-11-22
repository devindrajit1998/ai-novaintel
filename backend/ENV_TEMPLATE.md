# Environment Variables Template

Copy this to `backend/.env` and fill in your values:

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL=postgresql://user:password@localhost:5432/novaintel
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# LLM PROVIDER - GEMINI (Default)
# ============================================
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

# ============================================
# WEB SEARCH - GOOGLE CUSTOM SEARCH API
# ============================================
WEB_SEARCH_PROVIDER=google
GOOGLE_SEARCH_API_KEY=AIzaSyD4hZ3z90B-Qp8_oiOzkmTEyYCQ73g-zBg
GOOGLE_SEARCH_ENGINE_ID=your-custom-search-engine-id

# To get Custom Search Engine ID:
# 1. Go to https://programmablesearchengine.google.com/
# 2. Create a custom search engine
# 3. Copy the Search Engine ID (CX) from the settings

# ============================================
# EMBEDDING MODEL (OpenAI Recommended)
# ============================================
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=your-openai-api-key

# Alternative: Use HuggingFace (free)
# EMBEDDING_PROVIDER=huggingface
# EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2

# ============================================
# VECTOR DATABASE (ChromaDB Default)
# ============================================
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# Alternative: Qdrant
# VECTOR_DB_TYPE=qdrant
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=

# Alternative: Pinecone
# VECTOR_DB_TYPE=pinecone
# PINECONE_API_KEY=
# PINECONE_ENVIRONMENT=us-east-1
# PINECONE_INDEX_NAME=novaintel-documents

# ============================================
# OPTIONAL: RERANKING (Cohere)
# ============================================
COHERE_API_KEY=

# ============================================
# OPTIONAL: OTHER LLM PROVIDERS
# ============================================
# OPENAI_API_KEY=your-openai-api-key  # Also used for embeddings
# ANTHROPIC_API_KEY=your-claude-api-key

# ============================================
# OPTIONAL: LANGSMITH MONITORING
# ============================================
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=novaintel

# ============================================
# EMAIL CONFIGURATION (Optional)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:8080

# ============================================
# FILE STORAGE
# ============================================
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
ALLOWED_EXTENSIONS=.pdf,.docx

# ============================================
# CORS CONFIGURATION
# ============================================
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

## Quick Setup Instructions

1. **Gemini API Key**:
   - Get from: https://aistudio.google.com/app/apikey
   - Add to `GEMINI_API_KEY`

2. **Google Custom Search Engine ID**:
   - Go to: https://programmablesearchengine.google.com/
   - Create custom search engine
   - Copy Search Engine ID to `GOOGLE_SEARCH_ENGINE_ID`

3. **OpenAI API Key** (for embeddings):
   - Get from: https://platform.openai.com/api-keys
   - Add to `OPENAI_API_KEY`

4. **Generate Secret Key**:
   ```bash
   openssl rand -hex 32
   ```
   Add output to `SECRET_KEY`

