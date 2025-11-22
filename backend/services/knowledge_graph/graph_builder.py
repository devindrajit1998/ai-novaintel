"""
Knowledge graph builder for case study matching and relationship understanding.
"""
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.case_study import CaseStudy
from services.knowledge_graph.entity_extractor import entity_extractor, Entity, Relationship
import sys


class KnowledgeGraph:
    """Knowledge graph for storing entities and relationships."""
    
    def __init__(self):
        """Initialize knowledge graph."""
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # type -> entity names
        self.relationship_index: Dict[str, List[Relationship]] = defaultdict(list)  # entity -> relationships
    
    def add_entity(self, entity: Entity):
        """Add an entity to the graph."""
        self.entities[entity.name] = entity
        self.entity_index[entity.type].add(entity.name)
    
    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph."""
        self.relationships.append(relationship)
        self.relationship_index[relationship.source].append(relationship)
        # Add reverse relationship for bidirectional traversal
        reverse = Relationship(
            source=relationship.target,
            target=relationship.source,
            relationship_type=self._reverse_relationship_type(relationship.relationship_type),
            strength=relationship.strength,
            description=relationship.description
        )
        self.relationship_index[relationship.target].append(reverse)
    
    def _reverse_relationship_type(self, rel_type: str) -> str:
        """Get reverse relationship type."""
        reverse_map = {
            "uses": "used_by",
            "solves": "solved_by",
            "addresses": "addressed_by",
            "related_to": "related_to",  # Symmetric
            "in_industry": "contains_company"  # Approximate reverse
        }
        return reverse_map.get(rel_type, "related_to")
    
    def get_related_entities(self, entity_name: str, max_depth: int = 2) -> Set[str]:
        """Get entities related to a given entity within max_depth."""
        visited = set()
        to_visit = [(entity_name, 0)]
        related = set()
        
        while to_visit:
            current, depth = to_visit.pop(0)
            if current in visited or depth > max_depth:
                continue
            
            visited.add(current)
            if current != entity_name:
                related.add(current)
            
            # Get relationships from this entity
            for rel in self.relationship_index.get(current, []):
                if rel.target not in visited:
                    to_visit.append((rel.target, depth + 1))
        
        return related
    
    def find_similar_entities(self, entity_name: str, entity_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar entities based on relationships and types."""
        if entity_name not in self.entities:
            return []
        
        # Get related entities
        related = self.get_related_entities(entity_name, max_depth=2)
        
        # Score by relationship strength and type match
        scored = []
        for related_name in related:
            if related_name not in self.entities:
                continue
            
            related_entity = self.entities[related_name]
            
            # Calculate similarity score
            score = 0.0
            if related_entity.type == entity_type:
                score += 0.5
            
            # Add relationship strengths
            for rel in self.relationship_index.get(entity_name, []):
                if rel.target == related_name:
                    score += rel.strength
            
            scored.append({
                "entity": related_entity.model_dump(),
                "similarity_score": min(score, 1.0)
            })
        
        # Sort by score
        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return scored[:top_k]


class KnowledgeGraphBuilder:
    """Build and maintain knowledge graph from case studies and documents."""
    
    def __init__(self):
        """Initialize knowledge graph builder."""
        self.graph = KnowledgeGraph()
        self._initialize()
    
    def _initialize(self):
        """Initialize graph from existing case studies."""
        try:
            db = SessionLocal()
            try:
                # Load existing case studies
                case_studies = db.query(CaseStudy).filter(CaseStudy.indexed == True).all()
                
                print(f"[INFO] Loading {len(case_studies)} case studies into knowledge graph...", file=sys.stderr, flush=True)
                
                for case_study in case_studies:
                    self.add_case_study_to_graph(case_study, db)
                
                print(f"[OK] Knowledge graph initialized with {len(self.graph.entities)} entities and {len(self.graph.relationships)} relationships", file=sys.stderr, flush=True)
            finally:
                db.close()
        except Exception as e:
            print(f"[WARNING] Knowledge graph initialization failed: {e}", file=sys.stderr, flush=True)
    
    def add_case_study_to_graph(self, case_study: CaseStudy, db: Session):
        """Add a case study to the knowledge graph."""
        try:
            # Combine case study text
            text_parts = []
            if case_study.title:
                text_parts.append(f"Title: {case_study.title}")
            if case_study.industry:
                text_parts.append(f"Industry: {case_study.industry}")
            if case_study.description:
                text_parts.append(case_study.description)
            if case_study.project_description:
                text_parts.append(case_study.project_description)
            if case_study.impact:
                text_parts.append(f"Impact: {case_study.impact}")
            
            text = "\n".join(text_parts)
            
            # Extract entities and relationships
            result = entity_extractor.extract_entities(
                text=text,
                context=f"Case study in {case_study.industry} industry"
            )
            
            if result.get("error"):
                return
            
            # Add entities to graph
            for entity_data in result.get("entities", []):
                entity = Entity(**entity_data)
                
                # Add case study metadata
                entity.metadata["case_study_id"] = case_study.id
                entity.metadata["case_study_title"] = case_study.title
                entity.metadata["case_study_industry"] = case_study.industry
                
                self.graph.add_entity(entity)
            
            # Add relationships to graph
            for rel_data in result.get("relationships", []):
                relationship = Relationship(**rel_data)
                
                # Ensure both entities exist (add them if they don't)
                if relationship.source not in self.graph.entities:
                    # Create placeholder entity for source
                    source_entity = Entity(
                        name=relationship.source,
                        type="unknown",
                        description=None
                    )
                    source_entity.metadata["case_study_id"] = case_study.id
                    self.graph.add_entity(source_entity)
                
                if relationship.target not in self.graph.entities:
                    # Create placeholder entity for target
                    target_entity = Entity(
                        name=relationship.target,
                        type="unknown",
                        description=None
                    )
                    target_entity.metadata["case_study_id"] = case_study.id
                    self.graph.add_entity(target_entity)
                
                # Add relationship metadata
                relationship.metadata["case_study_id"] = case_study.id
                relationship.metadata["case_study_industry"] = case_study.industry
                
                self.graph.add_relationship(relationship)
        
        except Exception as e:
            print(f"[WARNING] Failed to add case study {case_study.id} to graph: {e}", file=sys.stderr, flush=True)
    
    def find_matching_case_studies(
        self,
        query_entities: List[str],
        query_industry: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find matching case studies based on entities in query.
        
        Args:
            query_entities: List of entity names from query
            query_industry: Optional industry filter
            top_k: Number of results to return
        
        Returns:
            List of matching case studies with scores
        """
        # Find related entities for each query entity
        all_related = set()
        for entity_name in query_entities:
            related = self.graph.get_related_entities(entity_name, max_depth=2)
            all_related.update(related)
            all_related.add(entity_name)
        
        # Group case studies by entity matches
        case_study_scores: Dict[int, float] = defaultdict(float)
        
        for entity_name in all_related:
            if entity_name in self.graph.entities:
                entity = self.graph.entities[entity_name]
                
                # Check if entity belongs to a case study
                case_study_id = entity.metadata.get("case_study_id")
                if case_study_id:
                    # Score based on entity type relevance
                    score = 1.0
                    if entity.type in ["challenge", "solution", "technology"]:
                        score = 1.5
                    
                    # Industry match bonus
                    # Get industry from case study metadata or from entity's case study reference
                    entity_industry = entity.metadata.get("case_study_industry")
                    if not entity_industry and entity.metadata.get("case_study_id"):
                        # Try to get industry from case study
                        try:
                            case_study = db.query(CaseStudy).filter(CaseStudy.id == entity.metadata.get("case_study_id")).first()
                            if case_study:
                                entity_industry = case_study.industry
                        except:
                            pass
                    
                    if query_industry and entity_industry and entity_industry.lower() == query_industry.lower():
                        score *= 1.5
                    
                    case_study_scores[case_study_id] += score
        
        # Sort by score
        sorted_case_studies = sorted(
            case_study_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Fetch case studies from database
        db = SessionLocal()
        try:
            results = []
            for case_study_id, score in sorted_case_studies:
                case_study = db.query(CaseStudy).filter(CaseStudy.id == case_study_id).first()
                if case_study:
                    results.append({
                        "id": case_study.id,
                        "title": case_study.title,
                        "industry": case_study.industry,
                        "impact": case_study.impact,
                        "description": case_study.description,
                        "graph_match_score": score
                    })
            
            return results
        finally:
            db.close()


# Global instance
knowledge_graph_builder = KnowledgeGraphBuilder()

