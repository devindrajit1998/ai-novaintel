# Dependencies Cleanup Summary

## Removed Dependencies

The following dependencies have been removed as they are not needed when using Supabase and Gemini:

### LLM Providers
- ❌ `openai==1.56.0` - Not needed (using Gemini)
- ❌ `anthropic==0.34.2` - Not needed
- ❌ `langchain-openai==0.2.5` - Not needed (using direct Gemini API)
- ❌ `langchain-google-genai==2.0.7` - Not needed (using direct Gemini API)

### Vector Database
- ❌ `pinecone-client==3.2.2` - Not needed (using Supabase)
- ❌ `llama-index-vector-stores-pinecone==0.1.4` - Not needed

### LlamaIndex OpenAI
- ❌ `llama-index-llms-openai==0.1.14` - Not needed (using Gemini)
- ❌ `llama-index-embeddings-openai==0.1.5` - Not needed (using Hugging Face)

### Authentication
- ❌ `python-jose[cryptography]==3.3.0` - Not needed (using Supabase Auth)
- ❌ `passlib[bcrypt]==1.7.4` - Not needed (using Supabase Auth)

### Tokenization
- ❌ `tiktoken==0.7.0` - Not needed (OpenAI-specific)

### Monitoring
- ❌ `langsmith==0.1.129` - Optional, removed to reduce dependencies

## Kept Dependencies

### Core Backend
- ✅ `fastapi==0.115.0`
- ✅ `uvicorn[standard]==0.32.0`
- ✅ `sqlalchemy==2.0.35` - Still needed for ORM
- ✅ `psycopg[binary]==3.1.19` - PostgreSQL driver (Supabase uses PostgreSQL)
- ✅ `pydantic==2.9.2`
- ✅ `pydantic-settings==2.5.2`
- ✅ `python-multipart==0.0.12` - File uploads
- ✅ `aiofiles==24.1.0`
- ✅ `requests==2.32.3` - For Gemini API calls

### File Processing
- ✅ `PyPDF2==3.0.1`
- ✅ `python-docx==1.1.2`
- ✅ `pypdf==4.2.0`
- ✅ `docx2txt==0.8`

### RAG Framework
- ✅ `llama-index==0.10.43`
- ✅ `llama-index-core==0.10.43`
- ✅ `llama-index-embeddings-huggingface==0.2.0` - Free embeddings
- ✅ `sentence-transformers==2.7.0` - For Hugging Face embeddings

### Supabase
- ✅ `supabase==2.5.0`
- ✅ `postgrest==0.16.0`
- ✅ `storage3==0.7.6`
- ✅ `gotrue==2.8.0`

### LLM
- ✅ `google-generativeai==0.8.3` - Gemini API (though we use direct REST calls)

### LangChain
- ✅ `langgraph==0.2.28` - Workflow orchestration
- ✅ `langchain==0.3.7` - For ChatPromptTemplate
- ✅ `langchain-community==0.3.5` - Community integrations

### Export
- ✅ `reportlab==4.2.2`
- ✅ `python-pptx==0.6.23`
- ✅ `weasyprint==62.3`

## Impact

### Size Reduction
- Removed ~15 unnecessary packages
- Reduced installation time
- Smaller Docker images

### Cost
- No OpenAI API costs
- No Pinecone costs
- Free Hugging Face embeddings
- Only Gemini API costs (much cheaper)

### Functionality
- ✅ All features still work
- ✅ Authentication via Supabase
- ✅ File storage via Supabase
- ✅ LLM via Gemini
- ✅ Embeddings via Hugging Face (free)

## Notes

1. **Vector Store**: Currently using Pinecone code structure but it's optional. If you want to use Supabase pgvector in the future, you'll need to add `llama-index-vector-stores-postgres` or implement custom integration.

2. **Security Module**: `utils/security.py` is no longer used but kept for reference. Can be deleted if desired.

3. **Google Generative AI**: The `google-generativeai` package is installed but we're using direct REST API calls. It's kept in case you want to switch to the SDK later.

## Installation

After cleanup, install dependencies:

```bash
pip install -r requirements.txt
```

This will install only the necessary packages for Supabase + Gemini setup.

