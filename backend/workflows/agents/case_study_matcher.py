"""
Case Study Matcher Agent - Uses RAG and knowledge graph to find similar case studies.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from db.database import get_db
from models.case_study import CaseStudy
from services.case_study_trainer import case_study_trainer
from services.knowledge_graph.graph_builder import knowledge_graph_builder
from services.knowledge_graph.entity_extractor import entity_extractor

class CaseStudyMatcherAgent:
    """Agent that matches case studies to challenges using RAG similarity search."""
    
    def __init__(self):
        pass
    
    def match_case_studies(
        self,
        challenges: List[Dict[str, Any]],
        db: Session,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Match case studies based on challenges using RAG similarity search.
        
        Args:
            challenges: List of challenges
            db: Database session
            top_k: Number of case studies to return
        
        Returns:
            dict with matching_case_studies list
        """
        try:
            # Handle None or empty challenges
            if not challenges:
                return {
                    "matching_case_studies": [],
                    "error": None
                }
            
            # Build query from challenges
            challenge_texts = []
            industries = set()
            
            # Extract entities from challenges using knowledge graph
            query_entities = []
            challenge_text = ""
            
            for ch in challenges:
                description = ch.get('description', '') or ch.get('text', '') or str(ch)
                category = ch.get('category', '') or ch.get('type', '')
                challenge_texts.append(f"{description} {category}")
                challenge_text += f"{description} {category}\n"
                
                # Extract industry hints
                category_lower = category.lower()
                if any(term in category_lower for term in ['bank', 'financial', 'bfsi', 'finance']):
                    industries.add('BFSI')
                elif 'retail' in category_lower:
                    industries.add('Retail')
                elif any(term in category_lower for term in ['health', 'medical', 'hospital']):
                    industries.add('Healthcare')
                elif 'manufactur' in category_lower:
                    industries.add('Manufacturing')
                elif 'tech' in category_lower:
                    industries.add('Technology')
            
            # Extract entities from challenges using knowledge graph entity extractor
            try:
                extraction_result = entity_extractor.extract_entities(
                    text=challenge_text,
                    context="Client challenges from RFP"
                )
                
                if not extraction_result.get("error"):
                    entities = extraction_result.get("entities", [])
                    query_entities = [e.get("name") for e in entities if e.get("name")]
            except Exception as e:
                print(f"[WARNING] Entity extraction failed: {e}")
                # Continue with RAG-only matching
            
            # Create search query
            query = ' '.join(challenge_texts[:5])  # Use first 5 challenges
            industry_filter = list(industries)[0] if industries else None
            
            # Try knowledge graph matching first (if entities extracted)
            matched = []
            if query_entities:
                try:
                    kg_results = knowledge_graph_builder.find_matching_case_studies(
                        query_entities=query_entities,
                        query_industry=industry_filter,
                        top_k=top_k
                    )
                    
                    # Format knowledge graph results
                    for cs in kg_results:
                        matched.append({
                            "id": cs.get("id"),
                            "title": cs.get("title"),
                            "industry": cs.get("industry"),
                            "impact": cs.get("impact"),
                            "description": cs.get("description"),
                            "project_description": cs.get("project_description"),
                            "relevance_score": cs.get("graph_match_score", 0.8),
                            "match_source": "knowledge_graph"
                        })
                except Exception as e:
                    print(f"[WARNING] Knowledge graph matching failed: {e}")
            
            # Use RAG to find similar case studies (complement or fallback)
            similar_case_studies = []
            try:
                similar_case_studies = case_study_trainer.find_similar_case_studies(
                    query=query,
                    industry=industry_filter,
                    top_k=top_k * 2  # Get more results to filter
                )
                
                # If we have industry filter and got no results, try without filter
                if not similar_case_studies and industry_filter:
                    similar_case_studies = case_study_trainer.find_similar_case_studies(
                        query=query,
                        industry=None,
                        top_k=top_k * 2
                    )
            except Exception as e:
                print(f"[WARNING] RAG matching failed: {e}")
            
            # Merge RAG results (avoid duplicates)
            matched_ids = {m['id'] for m in matched}
            for cs in similar_case_studies:
                cs_id = cs.get("id")
                if cs_id not in matched_ids:
                    matched.append({
                        "id": cs_id,
                        "title": cs.get("title"),
                        "industry": cs.get("industry"),
                        "impact": cs.get("impact"),
                        "description": cs.get("description"),
                        "project_description": cs.get("project_description"),
                        "relevance_score": cs.get("similarity_score", 0.7),
                        "match_source": "rag"
                    })
                    matched_ids.add(cs_id)
            
            # Sort by relevance score (knowledge graph results typically have higher scores)
            matched.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            
            # If we still don't have enough results, fallback to database query
            if len(matched) < top_k:
                all_case_studies = db.query(CaseStudy).filter(
                    CaseStudy.indexed == True  # Only indexed case studies
                ).limit(top_k - len(matched)).all()
                
                for case_study in all_case_studies:
                    if case_study.id not in matched_ids:
                        matched.append({
                            "id": case_study.id,
                            "title": case_study.title,
                            "industry": case_study.industry,
                            "impact": case_study.impact,
                            "description": case_study.description,
                            "project_description": case_study.project_description,
                            "relevance_score": 0.5,
                            "match_source": "database"
                        })
                        matched_ids.add(case_study.id)
            
            return {
                "matching_case_studies": matched[:top_k],
                "error": None
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "matching_case_studies": [],
                "error": str(e)
            }

# Global instance
case_study_matcher_agent = CaseStudyMatcherAgent()

