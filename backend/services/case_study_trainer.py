"""
Enhanced RAG-based service for processing and training case study documents.
"""
from typing import List, Dict, Any
from pathlib import Path
import os
import json
import re
from utils.text_extractor import TextExtractor
from utils.llm_factory import get_llm
from models.case_study import CaseStudy
from models.case_study_document import CaseStudyDocument, ProcessingStatus
from sqlalchemy.orm import Session
from rag.document_processor import document_processor
from rag.index_builder import index_builder
from rag.vector_store import vector_store_manager
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.schema import BaseNode

class CaseStudyTrainer:
    """Process and train case study documents with RAG indexing."""
    
    def __init__(self):
        self.text_extractor = TextExtractor()
    
    def process_case_study_document(
        self,
        document: CaseStudyDocument,
        db: Session
    ) -> Dict[str, Any]:
        """
        Process a case study document: extract text, analyze, create case study, and index in RAG.
        """
        try:
            # Step 1: Extract text
            document.processing_status = ProcessingStatus.EXTRACTING.value
            db.commit()
            
            extraction_result = self.text_extractor.extract_text(
                document.file_path,
                document.file_type
            )
            
            if not extraction_result.get('success'):
                document.processing_status = ProcessingStatus.FAILED.value
                document.error_message = extraction_result.get('error', 'Text extraction failed')
                db.commit()
                return {
                    "success": False,
                    "error": extraction_result.get('error', 'Text extraction failed')
                }
            
            # Save extracted text
            document.extracted_text = self.text_extractor.clean_text(
                extraction_result['text']
            )
            document.document_metadata = extraction_result.get('metadata', {})
            db.commit()
            
            # Step 2: Analyze and extract case study information
            document.processing_status = ProcessingStatus.ANALYZING.value
            db.commit()
            
            case_study_data = self._extract_case_study_info(
                document.extracted_text,
                document.filename
            )
            
            if not case_study_data.get('success'):
                document.processing_status = ProcessingStatus.FAILED.value
                document.error_message = case_study_data.get('error', 'Failed to extract case study info')
                db.commit()
                return {
                    "success": False,
                    "error": case_study_data.get('error', 'Failed to extract case study info')
                }
            
            # Step 3: Create or update case study
            case_study = self._create_case_study_from_data(
                case_study_data,
                document.user_id,
                db
            )
            
            # Link document to case study
            document.case_study_id = case_study.id
            db.commit()
            
            # Step 4: Index in RAG
            document.processing_status = ProcessingStatus.INDEXING.value
            db.commit()
            
            index_result = self._index_case_study_in_rag(
                case_study,
                document,
                db
            )
            
            if index_result.get('success'):
                case_study.indexed = True
                document.processing_status = ProcessingStatus.COMPLETED.value
                db.commit()
                
                # Add to knowledge graph
                try:
                    from services.knowledge_graph.graph_builder import knowledge_graph_builder
                    knowledge_graph_builder.add_case_study_to_graph(case_study, db)
                except Exception as e:
                    print(f"[WARNING] Failed to add case study to knowledge graph: {e}")
                    # Continue even if knowledge graph fails
                
                return {
                    "success": True,
                    "case_study_id": case_study.id,
                    "case_study": {
                        "id": case_study.id,
                        "title": case_study.title,
                        "industry": case_study.industry,
                        "impact": case_study.impact,
                        "description": case_study.description,
                        "project_description": case_study.project_description
                    },
                    "indexed": True
                }
            else:
                # Case study created but indexing failed
                document.processing_status = ProcessingStatus.COMPLETED.value
                document.error_message = f"Case study created but indexing failed: {index_result.get('error')}"
                db.commit()
                return {
                    "success": True,
                    "case_study_id": case_study.id,
                    "case_study": {
                        "id": case_study.id,
                        "title": case_study.title,
                        "industry": case_study.industry,
                        "impact": case_study.impact,
                        "description": case_study.description,
                        "project_description": case_study.project_description
                    },
                    "indexed": False,
                    "warning": index_result.get('error')
                }
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            document.processing_status = ProcessingStatus.FAILED.value
            document.error_message = str(e)
            db.commit()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_case_study_info(self, text: str, filename: str) -> Dict[str, Any]:
        """Use AI to extract case study information from text."""
        try:
            llm = get_llm()
            if not llm:
                return {"success": False, "error": "LLM not available"}
            
            from langchain_core.prompts import ChatPromptTemplate
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at analyzing case study documents. Extract key information from the document and return it in JSON format."""),
                ("user", """Analyze this case study document and extract:

1. Title - A clear, descriptive title
2. Industry - The industry/sector (e.g., BFSI, Healthcare, Retail, Technology)
3. Impact - Key metrics or outcomes (e.g., "45% Faster Processing", "30% Cost Reduction")
4. Description - A brief summary (2-3 sentences)
5. Project Description - A comprehensive detailed description of the project, challenges, solutions, and results (3-5 paragraphs)
6. Key Challenges - List of challenges addressed
7. Solutions - List of solutions implemented
8. Results - List of results/outcomes

Document Text:
{text}

Return JSON format:
{{
    "title": "Case Study Title",
    "industry": "Industry Name",
    "impact": "Key Impact Metric",
    "description": "Brief summary...",
    "project_description": "Detailed project description with challenges, solutions, and results...",
    "challenges": ["challenge1", "challenge2"],
    "solutions": ["solution1", "solution2"],
    "results": ["result1", "result2"]
}}""")
            ])
            
            chain = prompt | llm
            # Use more text for better extraction
            text_sample = text[:8000] if len(text) > 8000 else text
            response = chain.invoke({"text": text_sample})
            
            # Parse JSON response
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                case_study_data = json.loads(json_match.group())
                return {
                    "success": True,
                    **case_study_data
                }
            else:
                # Try to parse the entire response as JSON
                try:
                    case_study_data = json.loads(response_content)
                    return {
                        "success": True,
                        **case_study_data
                    }
                except:
                    return {"success": False, "error": "Could not parse AI response"}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _create_case_study_from_data(
        self,
        data: Dict[str, Any],
        user_id: int,
        db: Session
    ) -> CaseStudy:
        """Create a CaseStudy record from extracted data."""
        # Check if case study with same title exists
        existing = db.query(CaseStudy).filter(
            CaseStudy.title == data.get('title', '')
        ).first()
        
        if existing:
            # Update existing
            existing.industry = data.get('industry', existing.industry)
            existing.impact = data.get('impact', existing.impact)
            existing.description = data.get('description', existing.description)
            existing.project_description = data.get('project_description', existing.project_description)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new
            new_case_study = CaseStudy(
                title=data.get('title', 'Untitled Case Study'),
                industry=data.get('industry', 'General'),
                impact=data.get('impact', 'Positive Impact'),
                description=data.get('description', ''),
                project_description=data.get('project_description', '')
            )
            db.add(new_case_study)
            db.commit()
            db.refresh(new_case_study)
            return new_case_study
    
    def _index_case_study_in_rag(
        self,
        case_study: CaseStudy,
        document: CaseStudyDocument,
        db: Session
    ) -> Dict[str, Any]:
        """Index case study document in RAG for similarity search."""
        try:
            if not vector_store_manager.is_available():
                return {"success": False, "error": "Vector store not available"}
            
            # Create a comprehensive text for indexing
            index_text = f"""
Title: {case_study.title}
Industry: {case_study.industry}
Impact: {case_study.impact}
Description: {case_study.description}
Project Description: {case_study.project_description}
"""
            
            # Create LlamaIndex Document
            doc = Document(
                text=index_text,
                metadata={
                    'case_study_id': case_study.id,
                    'document_id': document.id,
                    'title': case_study.title,
                    'industry': case_study.industry,
                    'type': 'case_study',  # Mark as case study for filtering
                    'user_id': document.user_id
                }
            )
            
            # Process document into nodes
            nodes = document_processor.chunk_document(doc)
            
            if not nodes:
                return {"success": False, "error": "No nodes generated from case study"}
            
            # Index nodes in vector store
            try:
                storage_context = StorageContext.from_defaults(
                    vector_store=vector_store_manager.get_vector_store()
                )
                
                index = VectorStoreIndex(
                    nodes=nodes,
                    storage_context=storage_context,
                    show_progress=False
                )
                
                return {
                    "success": True,
                    "chunk_count": len(nodes),
                    "message": f"Case study indexed with {len(nodes)} chunks"
                }
            except Exception as e:
                return {"success": False, "error": f"Error indexing: {str(e)}"}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def find_similar_case_studies(
        self,
        query: str,
        industry: str = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar case studies using RAG similarity search.
        
        Args:
            query: Search query (e.g., project challenges, requirements)
            industry: Optional industry filter
            top_k: Number of results to return
        
        Returns:
            List of case study dicts with similarity scores
        """
        try:
            from rag.retriever import retriever
            
            # Retrieve similar nodes
            nodes = retriever.retrieve(query, top_k=top_k)
            
            # Filter for case studies only
            case_study_nodes = [
                node for node in nodes
                if node.node.metadata.get('type') == 'case_study'
            ]
            
            # If industry filter provided, filter by industry
            if industry:
                case_study_nodes = [
                    node for node in case_study_nodes
                    if node.node.metadata.get('industry') == industry
                ]
            
            # Get unique case study IDs
            case_study_ids = list(set([
                node.node.metadata.get('case_study_id')
                for node in case_study_nodes
                if node.node.metadata.get('case_study_id')
            ]))
            
            if not case_study_ids:
                return []
            
            # Fetch case studies from database
            from db.database import SessionLocal
            db = SessionLocal()
            try:
                case_studies = db.query(CaseStudy).filter(
                    CaseStudy.id.in_(case_study_ids)
                ).all()
                
                # Create result with scores
                result = []
                for case_study in case_studies:
                    # Find matching node for score
                    matching_node = next(
                        (node for node in case_study_nodes 
                         if node.node.metadata.get('case_study_id') == case_study.id),
                        None
                    )
                    
                    result.append({
                        "id": case_study.id,
                        "title": case_study.title,
                        "industry": case_study.industry,
                        "impact": case_study.impact,
                        "description": case_study.description,
                        "project_description": case_study.project_description,
                        "similarity_score": matching_node.score if matching_node and hasattr(matching_node, 'score') else None
                    })
                
                # Sort by similarity score
                result.sort(key=lambda x: x['similarity_score'] or 0, reverse=True)
                
                return result
            finally:
                db.close()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return []

# Global instance
case_study_trainer = CaseStudyTrainer()
