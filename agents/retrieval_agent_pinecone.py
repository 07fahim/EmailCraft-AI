"""
Template Retrieval Agent - Pinecone version.
Uses Pinecone for semantic search with sentence-transformers embeddings.
"""

import json
import logging
from typing import List
from pathlib import Path

from models.schemas import PersonaOutput, RetrievedTemplate, EmailTemplate
from utils.pinecone_utils import get_pinecone

logger = logging.getLogger(__name__)


class TemplateRetrievalAgent:
    """
    Template Retrieval Agent using Pinecone for semantic search.
    """
    
    def __init__(self, top_k: int = 3):
        """Initialize the retrieval agent."""
        self.top_k = top_k
        self.namespace = "templates"
        self.pinecone = get_pinecone()
        self.templates = []
        
        self._load_templates()
        
        if self.pinecone.is_available():
            self._index_templates()
    
    def _load_templates(self):
        """Load email templates from JSON."""
        templates_path = Path("data/email_templates.json")
        
        if not templates_path.exists():
            logger.warning("email_templates.json not found, creating default")
            self._create_default_templates()
            return
        
        try:
            with open(templates_path, "r", encoding="utf-8") as f:
                templates_data = json.load(f)
            self.templates = templates_data.get("templates", [])
            logger.info(f"✅ Loaded {len(self.templates)} email templates")
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self._create_default_templates()
    
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
        
        self.templates = default_templates["templates"]
        logger.info(f"✅ Created {len(self.templates)} default templates")
    
    def _index_templates(self):
        """Index templates in Pinecone."""
        if not self.templates:
            return
        
        ids = []
        texts = []
        metadatas = []
        
        for template in self.templates:
            template_id = template.get("id", f"template_{len(ids)}")
            search_text = f"{template.get('title', '')} {template.get('industry', '')} {template.get('use_case', '')} {template.get('subject_line', '')} {template.get('body', '')}"
            
            ids.append(template_id)
            texts.append(search_text)
            metadatas.append({
                "title": template.get("title", ""),
                "industry": template.get("industry", ""),
                "use_case": template.get("use_case", ""),
                "performance_score": template.get("performance_score", 0.0)
            })
        
        self.pinecone.upsert(ids, texts, metadatas, namespace=self.namespace)
        logger.info(f"✅ Indexed {len(ids)} templates in Pinecone")
    
    def retrieve(self, persona: PersonaOutput, product: str, industry: str) -> List[RetrievedTemplate]:
        """Retrieve relevant templates using semantic search."""
        
        # Build query
        query_text = f"{industry} {product} {persona.value_focus} {', '.join(persona.pain_points)} {persona.communication_style}"
        
        # If Pinecone available, use it
        if self.pinecone.is_available():
            results = self.pinecone.query(query_text, top_k=self.top_k, namespace=self.namespace)
            
            # Map results back to templates
            template_dict = {t["id"]: t for t in self.templates}
            
            retrieved = []
            for match in results:
                template_id = match.get("id", "")
                if template_id in template_dict:
                    template_data = template_dict[template_id]
                    retrieved.append(RetrievedTemplate(
                        template=EmailTemplate(**template_data),
                        similarity_score=match.get("score", 0.5)
                    ))
            
            logger.info(f"Retrieved {len(retrieved)} templates via Pinecone")
            return retrieved
        
        # Fallback: return first few templates
        retrieved = []
        for template in self.templates[:self.top_k]:
            retrieved.append(RetrievedTemplate(
                template=EmailTemplate(**template),
                similarity_score=0.5
            ))
        
        return retrieved
