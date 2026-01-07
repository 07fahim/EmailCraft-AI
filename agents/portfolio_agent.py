"""
Portfolio/Case Study Retrieval Agent - RAG-based portfolio matching.
Works with CSV portfolio format (Techstack, Links).
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from models.schemas import PersonaOutput, ScrapedJobData
from utils.chroma_utils import get_chroma_client, get_or_create_collection

logger = logging.getLogger(__name__)


class PortfolioRetrievalAgent:
    """
    Portfolio Retrieval Agent - RAG system for portfolio items (CSV-based).

    Responsibilities:
    - Load portfolio from CSV (Techstack, Links columns)
    - Store in ChromaDB for semantic search
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
            collection_name: ChromaDB collection name
            top_k: Number of portfolio items to retrieve
            min_similarity: Minimum similarity score (0.0-1.0) to include item
        """
        self.top_k = top_k
        self.collection_name = collection_name
        self.min_similarity = min_similarity
        self.portfolio_path = Path("data/my_portfolio.csv")

        # Initialize ChromaDB using shared utility
        self.client = get_chroma_client()
        self.collection = get_or_create_collection(self.client, collection_name)

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

        query_parts = []
        # Collect keywords for filtering (skills, technologies)
        filter_keywords = set()

        if scraped_job_data:
            if scraped_job_data.skills:
                query_parts.append(" ".join(scraped_job_data.skills[:8]))
                # Extract individual skill keywords for filtering
                for skill in scraped_job_data.skills[:10]:
                    # Split by common delimiters and add each keyword
                    for word in skill.lower().replace(',', ' ').replace('/', ' ').split():
                        if len(word) > 2:  # Skip very short words
                            filter_keywords.add(word)
            if scraped_job_data.keywords:
                query_parts.append(" ".join(scraped_job_data.keywords[:5]))
                for kw in scraped_job_data.keywords[:8]:
                    for word in kw.lower().replace(',', ' ').replace('/', ' ').split():
                        if len(word) > 2:
                            filter_keywords.add(word)
            if scraped_job_data.responsibilities:
                query_parts.append(" ".join(scraped_job_data.responsibilities[:2]))

        if persona:
            if persona.pain_points:
                query_parts.append(" ".join(persona.pain_points[:2]))
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
            logger.error(f"ChromaDB query failed: {e}")
            return []

        retrieved_items: List[Dict[str, Any]] = []
        skipped_items: List[str] = []

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
