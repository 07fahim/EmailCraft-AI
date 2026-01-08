"""
Portfolio Retrieval Agent - Pinecone version.
Uses Pinecone for semantic search with sentence-transformers embeddings.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import pandas as pd

from models.schemas import PersonaOutput, ScrapedJobData
from utils.pinecone_utils import get_pinecone

logger = logging.getLogger(__name__)


class PortfolioRetrievalAgent:
    """
    Portfolio Retrieval Agent using Pinecone for semantic search.
    """
    
    EXCLUDE_KEYWORDS = {
        'benefits', 'insurance', 'medical', 'dental', 'vision', 'vacation', 'pto',
        'paid', 'time', 'off', 'health', 'wellness', 'retirement', '401k', 'bonus',
        'salary', 'compensation', 'perks', 'flexible', 'remote', 'hybrid', 'onsite',
        'team', 'culture', 'environment', 'collaborative', 'dynamic', 'fast-paced',
        'startup', 'company', 'office', 'equity', 'stock', 'options', 'gym',
    }

    def __init__(self, top_k: int = 3):
        """Initialize the portfolio retrieval agent."""
        self.top_k = top_k
        self.portfolio_path = Path("data/my_portfolio.csv")
        self.namespace = "portfolio"
        self.pinecone = get_pinecone()
        
        # Initialize portfolio if Pinecone is available
        if self.pinecone.is_available():
            self._initialize_portfolio()
        else:
            logger.warning("Pinecone not available - portfolio search disabled")
    
    def _initialize_portfolio(self):
        """Load and index portfolio items."""
        if not self.portfolio_path.exists():
            logger.warning(f"Portfolio CSV not found at {self.portfolio_path}")
            return
        
        try:
            df = pd.read_csv(self.portfolio_path)
            
            if "Techstack" not in df.columns or "Links" not in df.columns:
                logger.error("CSV must have 'Techstack' and 'Links' columns")
                return
            
            ids = []
            texts = []
            metadatas = []
            
            for idx, row in df.iterrows():
                techstack = str(row["Techstack"]).strip()
                link = str(row["Links"]).strip()
                
                if not techstack or techstack == "nan":
                    continue
                if not link or link == "nan" or not link.startswith(("http://", "https://")):
                    continue
                
                ids.append(f"portfolio_{idx}")
                texts.append(techstack)
                metadatas.append({
                    "techstack": techstack,
                    "link": link
                })
            
            if ids:
                # Clear existing and upsert new
                self.pinecone.upsert(ids, texts, metadatas, namespace=self.namespace)
                logger.info(f"✅ Indexed {len(ids)} portfolio items in Pinecone")
                
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
    
    def retrieve(
        self,
        persona: Optional[PersonaOutput] = None,
        scraped_job_data: Optional[ScrapedJobData] = None,
        product: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant portfolio items using semantic search."""
        
        if not self.pinecone.is_available():
            logger.warning("Pinecone not available")
            return []
        
        # Build query
        query_parts = []
        
        if scraped_job_data:
            if scraped_job_data.skills:
                tech_skills = [s for s in scraped_job_data.skills[:10]
                              if not any(ex in s.lower() for ex in self.EXCLUDE_KEYWORDS)]
                if tech_skills:
                    query_parts.extend(tech_skills[:8])
            
            if scraped_job_data.keywords:
                tech_keywords = [kw for kw in scraped_job_data.keywords[:8]
                                if not any(ex in kw.lower() for ex in self.EXCLUDE_KEYWORDS)]
                if tech_keywords:
                    query_parts.extend(tech_keywords[:5])
            
            if scraped_job_data.role:
                query_parts.append(scraped_job_data.role)
        
        if persona and persona.pain_points:
            query_parts.extend(persona.pain_points[:2])
        
        if product:
            query_parts.append(product)
        if industry:
            query_parts.append(industry)
        
        query_text = " ".join(query_parts)
        
        if not query_text.strip():
            logger.warning("No query text for portfolio retrieval")
            return []
        
        logger.info(f"Portfolio query: {query_text[:100]}...")
        
        # Query Pinecone
        results = self.pinecone.query(query_text, top_k=self.top_k, namespace=self.namespace)
        
        # Format results
        retrieved_items = []
        for match in results:
            metadata = match.get("metadata", {})
            techstack = metadata.get("techstack", "")
            
            retrieved_items.append({
                "title": f"Project with {techstack}",
                "tech_stack": techstack,
                "description": f"Portfolio project showcasing expertise in {techstack}",
                "outcomes": "Demonstrated proficiency and practical experience",
                "link": metadata.get("link", "#"),
                "similarity_score": match.get("score", 0.0),
            })
            logger.info(f"✅ Matched: '{techstack[:50]}' (score: {match.get('score', 0):.3f})")
        
        logger.info(f"Retrieved {len(retrieved_items)} portfolio items via Pinecone")
        return retrieved_items
    
    def add_portfolio_item(self, techstack: str, link: str):
        """Add a new portfolio item."""
        if not techstack.strip():
            raise ValueError("Techstack cannot be empty")
        if not link.startswith(("http://", "https://")):
            raise ValueError("Link must start with http:// or https://")
        
        # Add to Pinecone
        if self.pinecone.is_available():
            new_id = f"portfolio_new_{hash(techstack) % 10000}"
            self.pinecone.upsert([new_id], [techstack], [{"techstack": techstack, "link": link}], namespace=self.namespace)
        
        # Persist to CSV
        if self.portfolio_path.exists():
            df = pd.read_csv(self.portfolio_path)
            new_row = pd.DataFrame([{"Techstack": techstack, "Links": link}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.portfolio_path, index=False)
        
        logger.info(f"Added portfolio item: {techstack[:50]}...")
