# RAG Engine Documentation

Complete RAG (Retrieval Augmented Generation) pipeline for NovaIntel using LlamaIndex and vector databases.

## Overview

The RAG engine enables:
- **Document Ingestion**: Extract text from PDF/DOCX files
- **Text Chunking**: Split documents into manageable chunks (300-500 tokens)
- **Embedding Generation**: Create vector embeddings using OpenAI's `text-embedding-3-large`
- **Vector Storage**: Store embeddings in Pinecone vector database
- **Retrieval**: Semantic search to find relevant context
- **Chat with RFP**: Query documents using natural language

## Architecture

```
┌─────────────┐
│   PDF/DOCX  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Text Extractor  │ → Extract & clean text
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Document        │ → Create LlamaIndex Document
│ Processor       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Node Parser     │ → Chunk into nodes (500 tokens, 50 overlap)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Embedding       │ → Generate embeddings (text-embedding-3-large)
│ Service         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Vector Store    │ → Store in Pinecone
│ (Pinecone)      │
└─────────────────┘
```

## Components

### 1. Text Extractor (`utils/text_extractor.py`)
- Extracts text from PDF using `pypdf`
- Extracts text from DOCX using `docx2txt`
- Cleans and normalizes text
- Extracts metadata (title, author, etc.)

### 2. Document Processor (`rag/document_processor.py`)
- Creates LlamaIndex Documents
- Chunks documents using `SentenceSplitter`
- Configurable chunk size (500 tokens) and overlap (50 tokens)
- Adds metadata to each chunk

### 3. Embedding Service (`rag/embedding_service.py`)
- Uses OpenAI's `text-embedding-3-large` model
- Generates 3072-dimensional embeddings
- Batch processing support

### 4. Vector Store Manager (`rag/vector_store.py`)
- Manages Pinecone connection
- Auto-creates index if it doesn't exist
- Handles vector storage and retrieval
- Supports metadata filtering

### 5. Index Builder (`rag/index_builder.py`)
- Builds vector indexes from documents
- Processes files end-to-end
- Updates database with extracted text
- Returns index metadata

### 6. Retriever (`rag/retriever.py`)
- Performs similarity search
- Returns top K results (default: 5)
- Filters by project_id
- Returns nodes with scores and metadata

### 7. Chat Service (`rag/chat_service.py`)
- Uses GPT-4-turbo for responses
- Retrieves relevant context using RAG
- Maintains conversation history
- Returns grounded answers with sources

## API Endpoints

### Build Index
```http
POST /rag/build-index
Content-Type: application/json

{
  "rfp_document_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "index_id": "project_1_rfp_123",
  "chunk_count": 45,
  "document_id": 123,
  "message": "Index built successfully with 45 chunks"
}
```

### Query RAG
```http
POST /rag/query
Content-Type: application/json

{
  "query": "What are the key requirements?",
  "project_id": 1,
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "text": "The system must support...",
      "score": 0.89,
      "metadata": {
        "project_id": 1,
        "rfp_document_id": 123,
        "chunk_index": 0
      }
    }
  ],
  "query": "What are the key requirements?"
}
```

### Chat with RFP
```http
POST /rag/chat
Content-Type: application/json

{
  "query": "What is the timeline for implementation?",
  "project_id": 1,
  "conversation_history": [
    {"role": "user", "content": "What are the requirements?"},
    {"role": "assistant", "content": "The requirements include..."}
  ],
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Based on the RFP document, the implementation timeline is...",
  "sources": [
    {
      "chunk_index": 1,
      "metadata": {...},
      "score": 0.92
    }
  ],
  "context_used": 5,
  "query": "What is the timeline for implementation?"
}
```

## Usage Flow

### 1. Upload RFP Document
```python
POST /upload/rfp?project_id=1
# Upload PDF/DOCX file
# Returns: rfp_document_id
```

### 2. Build Index
```python
POST /rag/build-index
{
  "rfp_document_id": 123
}
# Processes file, extracts text, chunks, generates embeddings, stores in vector DB
```

### 3. Query or Chat
```python
# Option A: Simple query
POST /rag/query
{
  "query": "What are the key challenges?",
  "project_id": 1
}

# Option B: Chat with context
POST /rag/chat
{
  "query": "How can we address these challenges?",
  "project_id": 1
}
```

## Configuration

### Environment Variables

```env
# OpenAI (for embeddings and chat)
OPENAI_API_KEY=your-openai-api-key

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=novaintel
```

### Chunking Parameters

Default settings in `document_processor.py`:
- **Chunk Size**: 500 tokens
- **Chunk Overlap**: 50 tokens
- **Separator**: Space

### Retrieval Parameters

Default settings in `retriever.py`:
- **Top K**: 5 results
- **Similarity Metric**: Cosine

## Performance Considerations

1. **Chunk Size**: 
   - Smaller chunks (300 tokens) = More precise retrieval, more chunks
   - Larger chunks (500 tokens) = More context per chunk, fewer chunks
   - Current: 500 tokens (balanced)

2. **Top K**:
   - More results = More context, higher cost
   - Current: 5 (optimal for most queries)

3. **Embedding Model**:
   - `text-embedding-3-large`: 3072 dimensions, high quality
   - Cost: ~$0.13 per 1M tokens

4. **LLM Model**:
   - `gpt-4-turbo-preview`: High quality responses
   - Temperature: 0.1 (deterministic, factual)

## Error Handling

All endpoints return structured error responses:
```json
{
  "success": false,
  "error": "Error message here"
}
```

Common errors:
- `Vector store not available`: Pinecone not configured
- `Embedding service not available`: OpenAI API key missing
- `File not found`: RFP document file missing
- `No relevant context found`: Query returned no results

## Future Enhancements

1. **Supabase Vector Support**: Add alternative vector database
2. **Hybrid Search**: Combine semantic + keyword search
3. **Re-ranking**: Use cross-encoder for better results
4. **Multi-document**: Support querying across multiple RFPs
5. **Streaming**: Stream chat responses
6. **Caching**: Cache frequent queries
7. **Analytics**: Track query patterns and performance

## Testing

Test the RAG pipeline:

```bash
# 1. Upload a file
curl -X POST "http://localhost:8000/upload/rfp?project_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_rfp.pdf"

# 2. Build index
curl -X POST "http://localhost:8000/rag/build-index" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rfp_document_id": 1}'

# 3. Query
curl -X POST "http://localhost:8000/rag/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the requirements?", "project_id": 1}'

# 4. Chat
curl -X POST "http://localhost:8000/rag/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the timeline", "project_id": 1}'
```

