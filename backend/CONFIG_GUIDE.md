# Configuration Guide

## LLM Provider: Gemini

The system is configured to use **Gemini** as the default LLM provider.

### Required Configuration

Add to your `backend/.env` file:

```env
# LLM Provider - Gemini (Required)
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

# Web Search - Google Custom Search API
WEB_SEARCH_PROVIDER=google
GOOGLE_SEARCH_API_KEY=AIzaSyD4hZ3z90B-Qp8_oiOzkmTEyYCQ73g-zBg
GOOGLE_SEARCH_ENGINE_ID=your-custom-search-engine-id
```

## Google Custom Search API Setup

1. **Enable Google Custom Search API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable "Custom Search API"
   - Create API key or use the provided key: `AIzaSyD4hZ3z90B-Qp8_oiOzkmTEyYCQ73g-zBg`

2. **Create Custom Search Engine**:
   - Go to [Google Custom Search](https://programmablesearchengine.google.com/)
   - Click "Create a custom search engine"
   - Add the sites you want to search (or leave blank to search entire web)
   - Copy your **Search Engine ID** and add it to `.env` as `GOOGLE_SEARCH_ENGINE_ID`

3. **Configuration**:
   ```env
   WEB_SEARCH_PROVIDER=google
   GOOGLE_SEARCH_API_KEY=AIzaSyD4hZ3z90B-Qp8_oiOzkmTEyYCQ73g-zBg
   GOOGLE_SEARCH_ENGINE_ID=your-custom-search-engine-id
   ```

## LLM Provider Configuration

The system supports intelligent routing to multiple LLM providers:

- **Gemini** (default) - Fast, cost-effective, good for most tasks
- **OpenAI GPT-4o** - High quality, better for complex reasoning
- **Claude 3.5** - Excellent reasoning, good for analysis

Even though Gemini is the default, the system will intelligently route specific tasks:
- Fast generation → Gemini
- Complex reasoning → Claude or GPT-4o
- High quality → GPT-4o or Claude
- Creative tasks → Claude

To use Gemini exclusively, set:
```env
LLM_PROVIDER=gemini
```

## Complete .env Example

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/novaintel
SECRET_KEY=your-secret-key

# LLM Provider - Gemini
GEMINI_API_KEY=your-gemini-api-key
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash

# Web Search - Google Custom Search API
WEB_SEARCH_PROVIDER=google
GOOGLE_SEARCH_API_KEY=AIzaSyD4hZ3z90B-Qp8_oiOzkmTEyYCQ73g-zBg
GOOGLE_SEARCH_ENGINE_ID=your-custom-search-engine-id

# Vector Database (default: ChromaDB)
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIR=./chroma_db

# Embeddings (default: OpenAI, but can use HuggingFace)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=your-openai-api-key  # Required for embeddings

# Optional: Reranking
COHERE_API_KEY=  # Optional, for better reranking

# Email (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:8080
```

