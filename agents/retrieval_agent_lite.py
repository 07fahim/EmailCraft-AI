"""
Template Retrieval Agent - Memory-efficient version using keyword matching.
Designed for free tier deployments with limited RAM.
"""

import json
import logging
from typing import List
from pathlib import Path

from models.schemas import PersonaOutput, RetrievedTemplate, EmailTemplate
from utils.simple_matching import tokenize, calculate_similarity

logger = logging.getLogger(__name__)


class TemplateRetrievalAgent:
    """
    Template Retrieval Agent - Lightweight template matching.
    
    Uses simple keyword matching instead of ChromaDB embeddings
    to stay within memory limits on free tier hosting.
    
    Responsibilities:
    - Load email templates from JSON
    - Keyword-based similarity search
    - Retrieve top-K relevant templates
    """
    
    def __init__(self, collection_name: str = "email_templates", top_k: int = 3):
        """Initialize the retrieval agent."""
        self.top_k = top_k
        self.templates = []
        self._load_templates()
    
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
    
    def retrieve(self, persona: PersonaOutput, product: str, industry: str) -> List[RetrievedTemplate]:
        """
        Retrieve relevant templates using keyword matching.
        
        Args:
            persona: PersonaOutput insights
            product: Product description
            industry: Target industry
            
        Returns:
            List of RetrievedTemplate objects
        """
        # Build query
        query_text = f"{industry} {product} {persona.value_focus} {', '.join(persona.pain_points)} {persona.communication_style}"
        query_tokens = tokenize(query_text)
        
        # Score each template
        scored_templates = []
        for template in self.templates:
            # Build searchable text for template
            template_text = f"{template.get('title', '')} {template.get('industry', '')} {template.get('use_case', '')} {template.get('subject_line', '')} {template.get('body', '')}"
            template_tokens = tokenize(template_text)
            
            # Calculate similarity
            similarity = calculate_similarity(query_tokens, template_tokens)
            
            # Boost by performance score (normalized 0-1)
            perf_score = template.get('performance_score', 5.0) / 10.0
            weighted_score = similarity * 0.7 + perf_score * 0.3
            
            scored_templates.append((template, weighted_score))
        
        # Sort by score and get top-k
        scored_templates.sort(key=lambda x: x[1], reverse=True)
        top_templates = scored_templates[:self.top_k]
        
        # Build result
        retrieved = []
        for template, score in top_templates:
            try:
                retrieved.append(RetrievedTemplate(
                    template=EmailTemplate(**template),
                    similarity_score=min(1.0, max(0.0, score))
                ))
            except Exception as e:
                logger.warning(f"Error creating template: {e}")
        
        logger.info(f"Retrieved {len(retrieved)} templates via keyword matching")
        return retrieved
