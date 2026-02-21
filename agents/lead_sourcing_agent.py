"""
Lead Sourcing Agent - Google Maps Scraping
Automates lead generation by scraping businesses from Google Maps.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LeadData:
    """Structured lead information."""
    company_name: str
    website: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    rating: Optional[float]
    reviews_count: Optional[int]
    category: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "company_name": self.company_name,
            "website": self.website,
            "phone": self.phone,
            "address": self.address,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "category": self.category
        }


class LeadSourcingAgent:
    """
    Lead Sourcing Agent using Apify (Google Maps).
    
    Workflow:
    1. Scrape businesses from Google Maps via Apify
    2. Filter businesses with websites
    3. Return lead data
    """
    
    def __init__(self):
        """Initialize with API credentials."""
        self.apify_api_key = os.getenv("APIFY_API_KEY")
        
        # Check if API is configured
        self.apify_enabled = bool(self.apify_api_key)
        
        if not self.apify_enabled:
            logger.warning("⚠️ APIFY_API_KEY not set - Google Maps scraping disabled")
    
    def scrape_google_maps(
        self,
        business_type: str,
        location: str,
        max_results: int = 20
    ) -> List[LeadData]:
        """
        Scrape businesses from Google Maps using Apify.
        
        Args:
            business_type: Type of business (e.g., "software companies", "restaurants")
            location: Location to search (e.g., "New York, NY", "San Francisco")
            max_results: Maximum number of results to return
            
        Returns:
            List of LeadData objects
        """
        if not self.apify_enabled:
            logger.error("❌ Apify API key not configured")
            return []
        
        try:
            from apify_client import ApifyClient
            
            logger.info(f"🔍 Scraping Google Maps: {business_type} in {location}")
            
            # Initialize Apify client
            client = ApifyClient(self.apify_api_key)
            
            # Prepare search query
            search_query = f"{business_type} in {location}"
            
            # Run the Google Maps scraper actor
            # Using the popular "compass/crawler-google-places" actor
            run_input = {
                "searchStringsArray": [search_query],
                "maxCrawledPlacesPerSearch": max_results,
                "language": "en",
                "includeWebsite": True,
                "includePhoneNumber": True,
                "includeReviews": False  # Skip reviews for faster scraping
            }
            
            # Start the actor and wait for it to finish
            run = client.actor("compass/crawler-google-places").call(run_input=run_input)
            
            # Fetch results
            leads = []
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                # Extract data from Apify result
                lead = LeadData(
                    company_name=item.get("title", "Unknown"),
                    website=item.get("website"),
                    phone=item.get("phone"),
                    address=item.get("address"),
                    rating=item.get("totalScore"),
                    reviews_count=item.get("reviewsCount"),
                    category=item.get("categoryName")
                )
                
                # Only include businesses with websites
                if lead.website:
                    leads.append(lead)
                    logger.info(f"✅ Found: {lead.company_name} - {lead.website}")
            
            logger.info(f"📊 Scraped {len(leads)} businesses with websites")
            return leads
            
        except ImportError:
            logger.error("❌ apify-client not installed. Run: pip install apify-client")
            return []
        except Exception as e:
            logger.error(f"❌ Error scraping Google Maps: {e}")
            return []
    
    def generate_leads(
        self,
        business_type: str,
        location: str,
        max_results: int = 20
    ) -> List[LeadData]:
        """
        Complete lead generation pipeline.
        
        Args:
            business_type: Type of business to search
            location: Location to search
            max_results: Maximum number of results
            
        Returns:
            List of LeadData objects
        """
        logger.info(f"🚀 Starting lead generation: {business_type} in {location}")
        
        # Scrape Google Maps
        leads = self.scrape_google_maps(business_type, location, max_results)
        
        if not leads:
            logger.warning("⚠️ No leads found from Google Maps")
            return []
        
        logger.info(f"✅ Lead generation complete: {len(leads)} leads")
        return leads
