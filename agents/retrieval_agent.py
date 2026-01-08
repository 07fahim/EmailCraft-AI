"""
Template Retrieval Agent - RAG-based template retrieval.
Auto-selects vector store: ChromaDB (local) or Pinecone (production).
"""

import json
import logging
from typing import List
from pathlib import Path

from models.schemas import PersonaOutput, RetrievedTemplate, EmailTemplate
from utils.vector_store import get_collection

logger = logging.getLogger(__name__)


class TemplateRetrievalAgent:
    """
    Template Retrieval Agent - RAG system for email templates.
    
    Responsibilities:
    - Store email templates in vector store
    - Semantic similarity search
    - Retrieve top-K relevant templates
    """
    
    def __init__(self, collection_name: str = "email_templates", top_k: int = 3):
        """Initialize the retrieval agent."""
        self.top_k = top_k
        self.collection_name = collection_name
        
        # Use unified vector store (auto-selects ChromaDB or Pinecone)
        self.collection = get_collection(collection_name)
        
        # Initialize templates if collection is empty
        if self.collection.count() == 0:
            self._initialize_templates()
    
    def _initialize_templates(self):
        """Load and index email templates from JSON."""
        templates_path = Path("data/email_templates.json")
        
        if not templates_path.exists():
            logger.warning("email_templates.json not found, creating default")
            self._create_default_templates()
            return
        
        with open(templates_path, "r", encoding="utf-8") as f:
            templates_data = json.load(f)
        
        ids = []
        documents = []
        metadatas = []
        
        for template in templates_data.get("templates", []):
            search_text = f"{template.get('title', '')} {template.get('industry', '')} {template.get('use_case', '')} {template.get('subject_line', '')} {template.get('body', '')}"
            
            ids.append(template.get("id", f"template_{len(ids)}"))
            documents.append(search_text)
            metadatas.append({
                "title": template.get("title", ""),
                "industry": template.get("industry", ""),
                "use_case": template.get("use_case", ""),
                "performance_score": template.get("performance_score", 0.0)
            })
        
        if ids:
            self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info(f"✅ Indexed {len(ids)} email templates")
    
    def _create_default_templates(self):
        """Create default email templates."""
        default_templates = {
            "templates": [
                {
                    "id": "template_1",
                    "title": "Problem-Solution B2B",
                    "industry": "Technology",
                    "use_case": "SaaS product intro",
                    "subject_line": "Quick question about {company}",
                    "body": "Hi {name},\n\nI noticed {company} is focused on {value}. Many {role}s struggle with {pain_point}.\n\n{product} solves this by {solution}.\n\nWould you be open to a brief chat?\n\nBest,\n{sender}",
                    "cta": "Schedule a 15-minute call",
                    "performance_score": 8.5
                },
                {
                    "id": "template_2",
                    "title": "Value-First Approach",
                    "industry": "General",
                    "use_case": "Product demo",
                    "subject_line": "How {company} can achieve {benefit}",
                    "body": "Hi {name},\n\n{product} has helped similar companies achieve {metric}.\n\nI'd love to show you how it works.\n\nInterested in a quick demo?\n\nBest,\n{sender}",
                    "cta": "Book a demo",
                    "performance_score": 8.0
                },
                {
                    "id": "template_3",
                    "title": "Social Proof",
                    "industry": "General",
                    "use_case": "Case study sharing",
                    "subject_line": "How {similar_company} solved {problem}",
                    "body": "Hi {name},\n\n{similar_company} recently used {product} to {achievement}.\n\nThought this might be relevant for {company}.\n\nWant to see the case study?\n\nBest,\n{sender}",
                    "cta": "View case study",
                    "performance_score": 7.5
                }
            ]
        }
        
        templates_path = Path("data/email_templates.json")
        templates_path.parent.mkdir(parents=True, exist_ok=True)
        with open(templates_path, "w", encoding="utf-8") as f:
            json.dump(default_templates, f, indent=2)
        
        self._initialize_templates()
    
    def retrieve(self, persona: PersonaOutput, product: str, industry: str) -> List[RetrievedTemplate]:
        """
        Retrieve relevant templates using RAG.
        
        Args:
            persona: PersonaOutput insights
            product: Product description
            industry: Target industry
            
        Returns:
            List of RetrievedTemplate objects
        """
        # Build query
        query_text = f"{industry} {product} {persona.value_focus} {', '.join(persona.pain_points)} {persona.communication_style}"
        
        # Semantic search
        results = self.collection.query(query_texts=[query_text], n_results=self.top_k)
        
        # Load full template data
        templates_path = Path("data/email_templates.json")
        if not templates_path.exists():
            return []
        
        with open(templates_path, "r", encoding="utf-8") as f:
            templates_data = json.load(f)
        
        template_dict = {t["id"]: t for t in templates_data.get("templates", [])}
        
        # Build result
        retrieved = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, template_id in enumerate(results["ids"][0]):
                if template_id in template_dict:
                    template_data = template_dict[template_id]
                    # Clamp similarity to valid range [0, 1]
                    raw_similarity = 1.0 - results["distances"][0][i] if results.get("distances") else 0.5
                    similarity = max(0.0, min(1.0, raw_similarity))
                    
                    retrieved.append(RetrievedTemplate(
                        template=EmailTemplate(**template_data),
                        similarity_score=similarity
                    ))
        
        return retrieved