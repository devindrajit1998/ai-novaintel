"""
Chat service for RAG-based conversations with RFP documents.
"""
import hashlib
from typing import List, Optional, Dict, Any
from rag.retriever import retriever
from utils.config import settings
from utils.gemini_service import gemini_service
from services.cache.rag_cache import rag_cache


class ChatService:
    """Service for chatting with RFP documents using RAG with caching."""
    
    def __init__(self):
        self.service = gemini_service
        self.cache = rag_cache
        self._initialize()
    
    def _initialize(self):
        """Initialize LLM."""
        if self.service.is_available():
            print(f"[OK] Chat service initialized: {settings.GEMINI_MODEL}")
        else:
            print("[WARNING] Gemini API key not configured")
    
    def is_available(self) -> bool:
        """Check if chat service is available."""
        return self.service.is_available()
    
    def _hash_conversation(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Create a hash of conversation history for cache key."""
        if not conversation_history:
            return "empty"
        # Create hash from last few messages (for context)
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        conv_str = str(recent_messages)
        return hashlib.md5(conv_str.encode()).hexdigest()[:16]
    

    # -------------------------------------------------------------------------
    #                               CHAT METHOD
    # -------------------------------------------------------------------------
    def chat(
        self,
        query: str,
        project_id: int,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        top_k: int = 5,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Chat with RFP document using RAG with caching.
        """

        if not self.is_available():
            return {
                'success': False,
                'error': 'Chat service not available',
                'answer': None,
                'sources': [],
                'context_used': 0,
                'query': query
            }

        # Check cache first
        if use_cache:
            conv_hash = self._hash_conversation(conversation_history)
            cached_response = self.cache.get_chat_response(query, project_id, conv_hash)
            if cached_response is not None:
                return cached_response

        # ------------------------------
        # Retrieve context chunks
        # ------------------------------
        nodes = retriever.retrieve(query, project_id, top_k, use_cache=use_cache)

        if not nodes:
            return {
                'success': False,
                'error': 'No relevant context found',
                'answer': None,
                'sources': [],
                'context_used': 0,
                'query': query
            }

        context_parts = []
        sources = []

        for i, node in enumerate(nodes, 1):
            text = node.node.get_content()
            metadata = node.node.metadata

            context_parts.append(f"[Context {i}]\n{text}")
            sources.append({
                'chunk_index': i,
                'metadata': metadata,
                'score': getattr(node, "score", None)
            })

        context = "\n\n".join(context_parts)

        # ------------------------------
        # SYSTEM PROMPT (Compact + Strong)
        # ------------------------------
        system_prompt = """
You are NovaIntel — an AI assistant specialized in RFP analysis and presales support.

STRICT RULES:
1. Use ONLY the provided RFP context, insights, and vector results.
2. If information is missing, respond EXACTLY with:
   "The provided RFP context does not contain this information."
3. Never hallucinate, assume, or fabricate details.
4. If user says "simplify" or "I don’t understand", rewrite in very simple words.
5. Be concise, factual, structured, and professional.

YOUR TASKS:
- Interpret RFP scope, requirements, eligibility, and evaluation criteria.
- Extract client challenges, risks, expectations.
- Generate discovery questions and value propositions.
- Summarize sections clearly.
- Help with proposal drafting.

GOAL:
Deliver the most accurate, context-grounded RFP insights possible.
"""

        # ------------------------------
        # USER PROMPT (Optimized)
        # ------------------------------
        user_prompt = f"""
Below is the retrieved RFP context. Use ONLY this information.

RFP CONTEXT:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer strictly based on the context above.
- Use structured formatting (bullet points, sections) when helpful.
- If unclear, ask for clarification.
"""

        # ------------------------------
        # Build message sequence
        # ------------------------------
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        messages.append({"role": "user", "content": user_prompt})

        # ------------------------------
        # Call Gemini
        # ------------------------------
        try:
            result = self.service.chat(messages, temperature=0.1)

            if result.get("error"):
                return {
                    'success': False,
                    'error': result["error"],
                    'answer': None,
                    'sources': sources,
                    'context_used': len(nodes),
                    'query': query
                }

            answer = result.get("content", "")

            response = {
                'success': True,
                'answer': answer,
                'sources': sources,
                'context_used': len(nodes),
                'query': query
            }
            
            # Cache response
            if use_cache:
                conv_hash = self._hash_conversation(conversation_history)
                self.cache.set_chat_response(query, project_id, conv_hash, response)
            
            return response

        except Exception as e:
            return {
                'success': False,
                'error': f"Error generating response: {str(e)}",
                'answer': None,
                'sources': sources,
                'context_used': len(nodes),
                'query': query
            }


# Global instance
chat_service = ChatService()
