"""
Portfolio/Case Study Retrieval Agent - Memory-efficient version using keyword matching.
Works with CSV portfolio format (Techstack, Links).
Designed for free tier deployments with limited RAM.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import pandas as pd

from models.schemas import PersonaOutput, ScrapedJobData
from utils.simple_matching import tokenize, calculate_similarity

logger = logging.getLogger(__name__)


class PortfolioRetrievalAgent:
    """
    Portfolio Retrieval Agent - Lightweight portfolio matching.
    
    Uses simple keyword matching instead of ChromaDB embeddings
    to stay within memory limits on free tier hosting.

    Responsibilities:
    - Load portfolio from CSV (Techstack, Links columns)
    - Keyword-based similarity search
    - Retrieve top-K relevant portfolio items based on job requirements
    """
    
    # Keywords to exclude (non-technical terms)
    EXCLUDE_KEYWORDS = {
        'benefits', 'insurance', 'medical', 'dental', 'vision', 'vacation', 'pto',
        'paid', 'time', 'off', 'health', 'wellness', 'retirement', '401k', 'bonus',
        'salary', 'compensation', 'perks', 'flexible', 'remote', 'hybrid', 'onsite',
        'team', 'culture', 'environment', 'collaborative', 'dynamic', 'fast-paced',
        'startup', 'company', 'office', 'equity', 'stock', 'options', 'gym',
        'lunch', 'snacks', 'meals', 'commuter', 'relocation', 'visa', 'sponsorship'
    }
    
    # Role to skills mapping for fallback
    ROLE_SKILL_MAP = {
        # Tech roles
        'software': ['python', 'java', 'javascript', 'react', 'node.js', 'sql'],
        'full stack': ['react', 'node.js', 'mongodb', 'javascript', 'typescript'],
        'frontend': ['react', 'angular', 'vue', 'javascript', 'typescript', 'css'],
        'backend': ['python', 'java', 'node.js', 'postgresql', 'mongodb', 'api'],
        'data scientist': ['python', 'machine learning', 'tensorflow', 'pandas', 'sql'],
        'data engineer': ['python', 'sql', 'spark', 'airflow', 'aws', 'etl'],
        'data analyst': ['sql', 'excel', 'python', 'tableau', 'power bi'],
        'machine learning': ['python', 'tensorflow', 'pytorch', 'machine learning'],
        'devops': ['docker', 'kubernetes', 'jenkins', 'aws', 'terraform', 'ci/cd'],
        'mobile': ['react native', 'flutter', 'ios', 'android', 'swift', 'kotlin'],
        'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform'],
        # Marketing roles
        'marketing': ['seo', 'google analytics', 'hubspot', 'content', 'social media'],
        'digital marketing': ['seo', 'ppc', 'google ads', 'facebook ads', 'analytics'],
        'content': ['content writing', 'copywriting', 'seo', 'cms', 'wordpress'],
        # Sales roles
        'sales': ['salesforce', 'crm', 'lead generation', 'b2b', 'negotiation'],
        'account': ['salesforce', 'account management', 'crm', 'client relations'],
        'business development': ['lead generation', 'crm', 'sales', 'partnerships'],
        # Finance roles
        'finance': ['excel', 'financial modeling', 'accounting', 'quickbooks', 'sap'],
        'accountant': ['quickbooks', 'excel', 'gaap', 'tax', 'bookkeeping'],
        'analyst': ['excel', 'sql', 'financial analysis', 'modeling', 'reporting'],
        # HR roles
        'hr': ['workday', 'recruiting', 'ats', 'employee relations', 'hris'],
        'recruiter': ['linkedin', 'ats', 'sourcing', 'interviewing', 'hiring'],
        # Design roles
        'designer': ['figma', 'adobe', 'sketch', 'ui/ux', 'photoshop'],
        'ux': ['figma', 'user research', 'wireframing', 'prototyping', 'usability'],
        # Operations roles
        'operations': ['project management', 'process improvement', 'erp', 'logistics'],
        'project manager': ['project management', 'agile', 'scrum', 'jira', 'pmp'],
        'product': ['product management', 'agile', 'roadmap', 'user stories', 'jira'],
    }

    def __init__(
        self,
        collection_name: str = "portfolio_items",
        top_k: int = 3,
        min_similarity: float = 0.0,
    ):
        """Initialize the portfolio retrieval agent."""
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.portfolio_path = Path("data/my_portfolio.csv")
        self.portfolio_items: List[Dict[str, Any]] = []
        
        self._load_portfolio()

    def _load_portfolio(self):
        """Load portfolio items from CSV file."""
        if not self.portfolio_path.exists():
            logger.warning(f"Portfolio CSV not found at {self.portfolio_path}")
            return

        try:
            df = pd.read_csv(self.portfolio_path)

            if "Techstack" not in df.columns or "Links" not in df.columns:
                logger.error("CSV must have 'Techstack' and 'Links' columns")
                return

            for idx, row in df.iterrows():
                techstack = str(row["Techstack"]).strip()
                link = str(row["Links"]).strip()

                if not techstack or techstack == "nan" or not link or link == "nan":
                    continue

                if not link.startswith(("http://", "https://")):
                    continue

                self.portfolio_items.append({
                    "id": f"portfolio_{idx}",
                    "techstack": techstack,
                    "link": link,
                    "tokens": tokenize(techstack)  # Pre-tokenize for faster search
                })

            logger.info(f"✅ Loaded {len(self.portfolio_items)} portfolio items from CSV")

        except Exception as e:
            logger.error(f"Error loading portfolio CSV: {e}")

    def _extract_filter_keywords(
        self,
        scraped_job_data: Optional[ScrapedJobData] = None,
        persona: Optional[PersonaOutput] = None,
        product: Optional[str] = None,
    ) -> Set[str]:
        """Extract keywords for filtering from job data."""
        filter_keywords: Set[str] = set()
        query_parts: List[str] = []

        if scraped_job_data:
            # Extract from skills
            if scraped_job_data.skills:
                tech_skills = [s for s in scraped_job_data.skills[:10] 
                              if not any(ex in s.lower() for ex in self.EXCLUDE_KEYWORDS)]
                for skill in tech_skills:
                    for word in skill.lower().replace(',', ' ').replace('/', ' ').split():
                        if len(word) > 2 and word not in self.EXCLUDE_KEYWORDS:
                            filter_keywords.add(word)
                if tech_skills:
                    query_parts.append(" ".join(tech_skills[:8]))
            
            # Extract from keywords
            if scraped_job_data.keywords:
                tech_keywords = [kw for kw in scraped_job_data.keywords[:8]
                                if not any(ex in kw.lower() for ex in self.EXCLUDE_KEYWORDS)]
                for kw in tech_keywords:
                    for word in kw.lower().replace(',', ' ').replace('/', ' ').split():
                        if len(word) > 2 and word not in self.EXCLUDE_KEYWORDS:
                            filter_keywords.add(word)
            
            # Fallback: infer from role
            if not filter_keywords and scraped_job_data.role:
                role_lower = scraped_job_data.role.lower()
                for role_key, skills in self.ROLE_SKILL_MAP.items():
                    if role_key in role_lower:
                        filter_keywords.update(skills[:4])
                        query_parts.append(" ".join(skills[:4]))
                        logger.info(f"📌 Inferred skills from role '{scraped_job_data.role}': {skills[:4]}")
                        break

        if product:
            for word in product.lower().replace(',', ' ').replace('/', ' ').split():
                if len(word) > 2:
                    filter_keywords.add(word)

        return filter_keywords

    def retrieve(
        self,
        persona: Optional[PersonaOutput] = None,
        scraped_job_data: Optional[ScrapedJobData] = None,
        product: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant portfolio items using keyword matching.
        """
        if not self.portfolio_items:
            logger.warning("No portfolio items loaded")
            return []

        # Extract filter keywords
        filter_keywords = self._extract_filter_keywords(scraped_job_data, persona, product)
        
        # Build query text
        query_parts = []
        if scraped_job_data:
            if scraped_job_data.skills:
                query_parts.extend(scraped_job_data.skills[:8])
            if scraped_job_data.keywords:
                query_parts.extend(scraped_job_data.keywords[:5])
        if persona and persona.pain_points:
            query_parts.extend(persona.pain_points[:2])
        if product:
            query_parts.append(product)
        if industry:
            query_parts.append(industry)

        query_text = " ".join(query_parts)
        query_tokens = tokenize(query_text)

        logger.info(f"Portfolio search query: {query_text[:100]}...")
        logger.info(f"Filter keywords: {list(filter_keywords)[:15]}")

        # Score each portfolio item
        scored_items = []
        for item in self.portfolio_items:
            techstack_lower = item["techstack"].lower()
            
            # Check keyword match
            keyword_match = False
            matched_keywords = []
            
            if filter_keywords:
                for keyword in filter_keywords:
                    if keyword in techstack_lower:
                        keyword_match = True
                        matched_keywords.append(keyword)
            else:
                keyword_match = True  # No filter = include all
            
            if not keyword_match:
                continue
            
            # Calculate similarity score
            similarity = calculate_similarity(query_tokens, item["tokens"])
            
            # Boost score for keyword matches
            keyword_boost = min(0.3, len(matched_keywords) * 0.1)
            final_score = similarity + keyword_boost
            
            scored_items.append({
                "item": item,
                "score": final_score,
                "matched_keywords": matched_keywords
            })

        # Sort by score and get top-k
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        top_items = scored_items[:self.top_k]

        # Build result
        retrieved_items = []
        for entry in top_items:
            item = entry["item"]
            retrieved_items.append({
                "title": f"Project with {item['techstack']}",
                "tech_stack": item["techstack"],
                "description": f"Portfolio project showcasing expertise in {item['techstack']}",
                "outcomes": "Demonstrated proficiency and practical experience",
                "link": item["link"],
                "similarity_score": min(1.0, entry["score"]),
            })
            logger.info(f"✅ Matched: '{item['techstack'][:50]}' (keywords: {entry['matched_keywords'][:3]})")

        logger.info(f"Retrieved {len(retrieved_items)} portfolio items via keyword matching")
        return retrieved_items

    def add_portfolio_item(self, techstack: str, link: str):
        """Add a new portfolio item."""
        if not techstack.strip():
            raise ValueError("Techstack cannot be empty")

        if not link.startswith(("http://", "https://")):
            raise ValueError("Link must start with http:// or https://")

        # Add to in-memory list
        new_item = {
            "id": f"portfolio_{len(self.portfolio_items)}",
            "techstack": techstack,
            "link": link,
            "tokens": tokenize(techstack)
        }
        self.portfolio_items.append(new_item)

        # Persist to CSV
        if self.portfolio_path.exists():
            df = pd.read_csv(self.portfolio_path)
            new_row = pd.DataFrame([{"Techstack": techstack, "Links": link}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.portfolio_path, index=False)

        logger.info(f"Added portfolio item: {techstack[:50]}...")
