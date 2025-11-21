"""
Pydantic schemas for RAG endpoints.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BuildIndexRequest(BaseModel):
    rfp_document_id: int

class BuildIndexResponse(BaseModel):
    success: bool
    index_id: Optional[str] = None
    chunk_count: Optional[int] = None
    document_id: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    project_id: int
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]] = []
    query: str
    error: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    project_id: int
    conversation_history: Optional[List[Dict[str, str]]] = None
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    context_used: Optional[int] = None
    query: str
    error: Optional[str] = None

