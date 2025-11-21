"""
Case Study Matcher Agent - Uses RAG to find similar case studies.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from db.database import get_db
from models.case_study import CaseStudy
from services.case_study_trainer import case_study_trainer

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
            
            for ch in challenges:
                description = ch.get('description', '') or ch.get('text', '') or str(ch)
                category = ch.get('category', '') or ch.get('type', '')
                challenge_texts.append(f"{description} {category}")
                
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
            
            # Create search query
            query = ' '.join(challenge_texts[:5])  # Use first 5 challenges
            
            # Use RAG to find similar case studies
            # Try with industry filter first if we have industry hints
            industry_filter = list(industries)[0] if industries else None
            similar_case_studies = case_study_trainer.find_similar_case_studies(
                query=query,
                industry=industry_filter,
                top_k=top_k * 2  # Get more results to filter
            )
            
            # If we have industry filter and got results, use them
            # Otherwise, try without industry filter
            if not similar_case_studies and industry_filter:
                similar_case_studies = case_study_trainer.find_similar_case_studies(
                    query=query,
                    industry=None,
                    top_k=top_k * 2
                )
            
            # Format results
            matched = []
            for cs in similar_case_studies[:top_k]:
                matched.append({
                    "id": cs.get("id"),
                    "title": cs.get("title"),
                    "industry": cs.get("industry"),
                    "impact": cs.get("impact"),
                    "description": cs.get("description"),
                    "project_description": cs.get("project_description"),
                    "relevance_score": cs.get("similarity_score", 0.8)
                })
            
            # If RAG didn't return enough results, fallback to database query
            if len(matched) < top_k:
                all_case_studies = db.query(CaseStudy).filter(
                    CaseStudy.indexed == True  # Only indexed case studies
                ).limit(top_k - len(matched)).all()
                
                for case_study in all_case_studies:
                    if not any(m['id'] == case_study.id for m in matched):
                        matched.append({
                            "id": case_study.id,
                            "title": case_study.title,
                            "industry": case_study.industry,
                            "impact": case_study.impact,
                            "description": case_study.description,
                            "project_description": case_study.project_description,
                            "relevance_score": 0.5
                        })
            
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

