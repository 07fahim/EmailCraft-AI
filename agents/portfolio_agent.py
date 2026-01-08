"""
Portfolio/Case Study Retrieval Agent - RAG-based portfolio matching.
Works with CSV portfolio format (Techstack, Links).
Auto-selects vector store: ChromaDB (local) or Pinecone (production).
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from models.schemas import PersonaOutput, ScrapedJobData
from utils.vector_store import get_collection

logger = logging.getLogger(__name__)


class PortfolioRetrievalAgent:
    """
    Portfolio Retrieval Agent - RAG system for portfolio items (CSV-based).

    Responsibilities:
    - Load portfolio from CSV (Techstack, Links columns)
    - Store in vector store for semantic search
    - Retrieve top-K relevant portfolio items based on job requirements
    """

    def __init__(
        self,
        collection_name: str = "portfolio_items",
        top_k: int = 3,
        min_similarity: float = 0.0,  # Disabled - always return top-k items
    ):
        """
        Initialize the portfolio retrieval agent.

        Args:
            collection_name: Vector store collection name
            top_k: Number of portfolio items to retrieve
            min_similarity: Minimum similarity score (0.0-1.0) to include item
        """
        self.top_k = top_k
        self.collection_name = collection_name
        self.min_similarity = min_similarity
        self.portfolio_path = Path("data/my_portfolio.csv")

        # Initialize vector store (auto-selects ChromaDB or Pinecone)
        self.collection = get_collection(collection_name)

        # Initialize with portfolio data if empty
        if self.collection.count() == 0:
            self._initialize_portfolio()

    def _initialize_portfolio(self):
        """Load and index portfolio items from CSV file."""
        if not self.portfolio_path.exists():
            raise FileNotFoundError(
                f"Portfolio CSV not found at {self.portfolio_path}\n"
                f"Please create 'data/my_portfolio.csv' with columns: Techstack, Links\n"
                f"Example:\n"
                f"  Techstack,Links\n"
                f"  Python FastAPI PostgreSQL,https://github.com/user/project1\n"
                f"  React TypeScript Redux,https://github.com/user/project2"
            )

        try:
            df = pd.read_csv(self.portfolio_path)

            if "Techstack" not in df.columns or "Links" not in df.columns:
                raise ValueError(
                    "CSV must have 'Techstack' and 'Links' columns\n"
                    f"Found columns: {', '.join(df.columns)}"
                )

            if len(df) == 0:
                raise ValueError("Portfolio CSV is empty. Please add at least one project.")

            ids = []
            documents = []
            metadatas = []

            for idx, row in df.iterrows():
                techstack = str(row["Techstack"]).strip()
                link = str(row["Links"]).strip()

                if not techstack or techstack == "nan" or not link or link == "nan":
                    logger.warning(f"Skipping row {idx + 2}: empty techstack or link")
                    continue

                if not link.startswith(("http://", "https://")):
                    logger.warning(
                        f"Skipping row {idx + 2}: invalid link format '{link}'"
                    )
                    continue

                ids.append(f"portfolio_{idx}")
                documents.append(techstack)
                metadatas.append(
                    {
                        "techstack": techstack,
                        "link": link,
                    }
                )

            if not ids:
                raise ValueError(
                    "No valid portfolio items found in CSV\n"
                    "Check that:\n"
                    "  - Techstack column is not empty\n"
                    "  - Links start with http:// or https://"
                )

            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"✅ Indexed {len(ids)} portfolio items from CSV")

        except Exception as e:
            logger.error(f"Error loading portfolio CSV: {e}")
            raise

    def retrieve(
        self,
        persona: Optional[PersonaOutput] = None,
        scraped_job_data: Optional[ScrapedJobData] = None,
        product: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant portfolio items using RAG + keyword filtering.
        """
        
        # Keywords to exclude (non-technical terms that shouldn't be used for matching)
        EXCLUDE_KEYWORDS = {
            'benefits', 'insurance', 'medical', 'dental', 'vision', 'vacation', 'pto',
            'paid', 'time', 'off', 'health', 'wellness', 'retirement', '401k', 'bonus',
            'salary', 'compensation', 'perks', 'flexible', 'remote', 'hybrid', 'onsite',
            'team', 'culture', 'environment', 'collaborative', 'dynamic', 'fast-paced',
            'startup', 'company', 'office', 'equity', 'stock', 'options', 'gym',
            'lunch', 'snacks', 'meals', 'commuter', 'relocation', 'visa', 'sponsorship'
        }

        query_parts = []
        # Collect keywords for filtering (skills, technologies)
        filter_keywords = set()

        if scraped_job_data:
            if scraped_job_data.skills:
                # Filter out non-technical skills
                tech_skills = [s for s in scraped_job_data.skills[:10] 
                              if not any(exclude in s.lower() for exclude in EXCLUDE_KEYWORDS)]
                if tech_skills:
                    query_parts.append(" ".join(tech_skills[:8]))
                    # Extract individual skill keywords for filtering
                    for skill in tech_skills:
                        # Split by common delimiters and add each keyword
                        for word in skill.lower().replace(',', ' ').replace('/', ' ').split():
                            if len(word) > 2 and word not in EXCLUDE_KEYWORDS:
                                filter_keywords.add(word)
            
            if scraped_job_data.keywords:
                # Filter keywords to only include tech-related terms
                tech_keywords = [kw for kw in scraped_job_data.keywords[:8]
                                if not any(exclude in kw.lower() for exclude in EXCLUDE_KEYWORDS)]
                if tech_keywords:
                    query_parts.append(" ".join(tech_keywords[:5]))
                    for kw in tech_keywords:
                        for word in kw.lower().replace(',', ' ').replace('/', ' ').split():
                            if len(word) > 2 and word not in EXCLUDE_KEYWORDS:
                                filter_keywords.add(word)
            
            # Use responsibilities but filter out benefits-related content
            if scraped_job_data.responsibilities:
                tech_responsibilities = [r for r in scraped_job_data.responsibilities[:3]
                                        if not any(exclude in r.lower() for exclude in EXCLUDE_KEYWORDS)]
                if tech_responsibilities:
                    query_parts.append(" ".join(tech_responsibilities[:2]))
            
            # ALWAYS check role-based skill inference (scraped skills may be wrong)
            if scraped_job_data.role:
                role_lower = scraped_job_data.role.lower()
                
                # Known tech skills that indicate real extraction worked
                REAL_TECH_SKILLS = {
                    'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
                    'typescript', 'sql', 'mongodb', 'postgresql', 'mysql', 'docker',
                    'kubernetes', 'aws', 'azure', 'gcp', 'spring', 'django', 'flask',
                    'tensorflow', 'pytorch', 'c++', 'c#', 'ruby', 'go', 'rust', 'php',
                    'html', 'css', 'graphql', 'redis', 'elasticsearch', 'kafka',
                    'git', 'linux', 'jenkins', 'terraform', 'ansible', 'ci/cd',
                    'figma', 'photoshop', 'salesforce', 'hubspot', 'excel', 'tableau',
                    'power bi', 'sap', 'oracle', 'workday', 'jira', 'confluence'
                }
                
                # Check if we have any REAL tech skills in filter_keywords
                has_real_skills = any(kw in REAL_TECH_SKILLS for kw in filter_keywords)
                
                # If no real skills extracted, use role-based inference
                if not has_real_skills:
                    logger.info(f"⚠️ No real tech skills found in: {list(filter_keywords)[:5]}. Using role-based inference.")
                    # Clear bad keywords
                    filter_keywords.clear()
                    
                    # Generic role-to-skills mapping for various industries
                    role_skill_map = {
                        # Tech roles
                        'software': ['python', 'java', 'javascript', 'react', 'node.js', 'sql', 'backend', 'frontend'],
                        'engineer': ['python', 'java', 'javascript', 'sql', 'docker', 'aws'],
                        'developer': ['python', 'java', 'javascript', 'react', 'node.js', 'sql'],
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
                        'social media': ['social media', 'instagram', 'tiktok', 'content creation'],
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
                        'talent': ['recruiting', 'talent acquisition', 'ats', 'sourcing'],
                        # Design roles
                        'designer': ['figma', 'adobe', 'sketch', 'ui/ux', 'photoshop'],
                        'ux': ['figma', 'user research', 'wireframing', 'prototyping', 'usability'],
                        'graphic': ['photoshop', 'illustrator', 'indesign', 'branding', 'design'],
                        # Operations roles
                        'operations': ['project management', 'process improvement', 'erp', 'logistics'],
                        'project manager': ['project management', 'agile', 'scrum', 'jira', 'pmp'],
                        'product': ['product management', 'agile', 'roadmap', 'user stories', 'jira'],
                        'supply chain': ['supply chain', 'logistics', 'inventory', 'erp', 'procurement'],
                        # Healthcare roles
                        'nurse': ['patient care', 'emr', 'clinical', 'nursing', 'healthcare'],
                        'healthcare': ['emr', 'hipaa', 'patient care', 'clinical', 'medical'],
                        'medical': ['medical coding', 'emr', 'healthcare', 'clinical', 'patient'],
                        # Education roles
                        'teacher': ['curriculum', 'instruction', 'classroom', 'education', 'teaching'],
                        'instructor': ['training', 'curriculum', 'lms', 'e-learning', 'instruction'],
                        # Customer service
                        'customer': ['customer service', 'crm', 'zendesk', 'support', 'communication'],
                        'support': ['customer support', 'ticketing', 'zendesk', 'troubleshooting'],
                    }
                    
                    matched_role = False
                    for role_key, skills in role_skill_map.items():
                        if role_key in role_lower:
                            filter_keywords.update(skills[:5])
                            query_parts.append(" ".join(skills[:5]))
                            logger.info(f"📌 Inferred skills from role '{scraped_job_data.role}': {skills[:5]}")
                            matched_role = True
                            break
                    
                    # If no specific role matched, default to general software skills
                    if not matched_role and ('software' in role_lower or 'engineer' in role_lower or 'developer' in role_lower):
                        default_skills = ['python', 'java', 'javascript', 'react', 'sql', 'node.js']
                        filter_keywords.update(default_skills)
                        query_parts.append(" ".join(default_skills))
                        logger.info(f"📌 Using default software skills for '{scraped_job_data.role}'")

        if persona:
            if persona.pain_points:
                # Filter out non-tech pain points
                tech_pain_points = [p for p in persona.pain_points[:2] 
                                   if not any(exclude in p.lower() for exclude in EXCLUDE_KEYWORDS)]
                if tech_pain_points:
                    query_parts.append(" ".join(tech_pain_points))
            if persona.value_focus:
                query_parts.append(persona.value_focus)

        if product:
            query_parts.append(product)
            # Add role keywords
            for word in product.lower().replace(',', ' ').replace('/', ' ').split():
                if len(word) > 2:
                    filter_keywords.add(word)
        if industry:
            query_parts.append(industry)

        query_text = " ".join(query_parts)

        if not query_text.strip():
            logger.warning("No query text available for portfolio retrieval")
            return []

        logger.info(f"Portfolio search query: {query_text[:100]}...")
        logger.info(f"Filter keywords: {list(filter_keywords)[:15]}")

        try:
            # Get more results to filter from
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(self.top_k * 3, 10),  # Get more to filter
            )
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []

        retrieved_items: List[Dict[str, Any]] = []
        skipped_items: List[str] = []
        
        # Common professional keywords across industries
        COMMON_SKILL_KEYWORDS = {
            # Tech
            'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
            'typescript', 'sql', 'mongodb', 'postgresql', 'mysql', 'docker',
            'kubernetes', 'aws', 'azure', 'gcp', 'spring', 'django', 'flask',
            'tensorflow', 'pytorch', 'machine', 'learning', 'backend', 'frontend',
            'full-stack', 'fullstack', 'mobile', 'ios', 'android', 'kotlin', 'swift',
            # Marketing
            'seo', 'analytics', 'hubspot', 'marketing', 'content', 'social',
            'advertising', 'ppc', 'campaigns', 'branding',
            # Sales
            'salesforce', 'crm', 'sales', 'b2b', 'lead', 'account',
            # Finance
            'excel', 'financial', 'accounting', 'quickbooks', 'sap', 'modeling',
            # HR
            'recruiting', 'workday', 'ats', 'talent', 'hiring',
            # Design
            'figma', 'adobe', 'photoshop', 'illustrator', 'ui', 'ux', 'design',
            # Project Management
            'agile', 'scrum', 'jira', 'project', 'management', 'pmp',
            # General
            'communication', 'leadership', 'strategy', 'analysis', 'reporting'
        }

        if results.get("ids") and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                metadata = results["metadatas"][0][i]
                techstack = metadata.get("techstack", "")
                techstack_lower = techstack.lower()
                
                distance = (
                    results["distances"][0][i]
                    if results.get("distances")
                    else 0.5
                )
                
                # Check if portfolio item matches any filter keywords
                matches_keyword = False
                matched_keywords = []
                
                if filter_keywords:
                    for keyword in filter_keywords:
                        if keyword in techstack_lower:
                            matches_keyword = True
                            matched_keywords.append(keyword)
                    
                    # FALLBACK: If no keyword match but high similarity score, still include
                    if not matches_keyword and distance < 0.8:
                        # Check if it matches any common skill keyword
                        for common_kw in COMMON_SKILL_KEYWORDS:
                            if common_kw in techstack_lower:
                                matches_keyword = True
                                matched_keywords.append(f"~{common_kw}")  # Mark as fallback match
                                break
                else:
                    # No filter keywords - include all
                    matches_keyword = True
                
                if not matches_keyword:
                    skipped_items.append(techstack[:40])
                    continue
                
                # Stop if we have enough items
                if len(retrieved_items) >= self.top_k:
                    break

                similarity = max(0.0, min(1.0, 1.0 - distance))

                retrieved_items.append(
                    {
                        "title": f"Project with {techstack}",
                        "tech_stack": techstack,
                        "description": (
                            f"Portfolio project showcasing expertise in "
                            f"{techstack}"
                        ),
                        "outcomes": "Demonstrated proficiency and practical experience",
                        "link": metadata.get("link", "#"),
                        "similarity_score": similarity,
                    }
                )

                logger.info(
                    f"✅ Matched: '{techstack[:50]}' "
                    f"(keywords: {matched_keywords[:3]}, distance: {distance:.2f})"
                )
        
        if skipped_items:
            logger.info(f"⏭️ Skipped irrelevant: {skipped_items[:5]}")

        logger.info(f"Retrieved {len(retrieved_items)} relevant portfolio items")
        return retrieved_items

    def add_portfolio_item(self, techstack: str, link: str):
        """
        Add a new portfolio item to the collection.
        """
        if not techstack.strip():
            raise ValueError("Techstack cannot be empty")

        if not link.startswith(("http://", "https://")):
            raise ValueError("Link must start with http:// or https://")

        portfolio_id = f"portfolio_{self.collection.count()}"

        self.collection.add(
            ids=[portfolio_id],
            documents=[techstack],
            metadatas=[{"techstack": techstack, "link": link}],
        )

        if self.portfolio_path.exists():
            df = pd.read_csv(self.portfolio_path)
            new_row = pd.DataFrame([{"Techstack": techstack, "Links": link}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.portfolio_path, index=False)

        logger.info(f"Added portfolio item: {techstack[:50]}...")
