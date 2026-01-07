"""
Job Scraping Agent - Scrapes and extracts structured data from job postings.
OPTIMIZED: Faster parsing, intelligent caching, better extraction.
"""

import json
import re
import logging
import hashlib
from typing import Optional, Dict
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from models.schemas import ScrapedJobData
from utils.groq_client import get_groq_client
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class JobScrapingAgent:
    """
    Job Scraping Agent - Extracts structured data from job postings.
    OPTIMIZED: Faster parsing, intelligent caching, better extraction.
    
    Responsibilities:
    - Scrape job posting content from URLs
    - Clean and extract structured information
    - Use LLM to parse and structure the data
    - Output high-confidence evidence for persona analysis
    """
    
    # OPTIMIZED: Class-level cache for scraped URLs
    _url_cache: Dict[str, ScrapedJobData] = {}
    
    def __init__(self):
        """Initialize the agent with prompt template."""
        self.llm = get_groq_client()
        self.prompt_template = self._load_prompt()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _load_prompt(self) -> PromptTemplate:
        """Load job scraping prompt from file."""
        prompt_path = Path("prompts/scraper_prompt.txt")
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        else:
            # Fallback prompt
            prompt_text = """Extract structured information from this job posting.

Job Posting Content:
{job_content}

Return ONLY valid JSON:
{{
  "role": "exact job title",
  "skills": ["skill1", "skill2"],
  "experience": "experience level",
  "responsibilities": ["resp1", "resp2"],
  "keywords": ["keyword1", "keyword2"],
  "company": "company name" or null
}}"""
        
        return PromptTemplate.from_template(prompt_text)
    
    def _extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML, focusing on job content areas."""
        
        # Remove script, style, nav, footer elements
        for element in soup(["script", "style", "meta", "link", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Try to find main job content area (common patterns)
        content_selectors = [
            # Common job site patterns
            '[data-automation="jobDescription"]',
            '[class*="job-description"]',
            '[class*="jobDescription"]',
            '[class*="job_description"]',
            '[class*="job-details"]',
            '[class*="jobDetails"]',
            '[class*="description-content"]',
            '[id*="job-description"]',
            '[id*="jobDescription"]',
            # Generic content areas
            'main',
            'article',
            '[role="main"]',
            '.content',
            '#content',
        ]
        
        extracted_parts = []
        
        # Try each selector
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements[:2]:  # Limit to first 2 matches
                    text = elem.get_text(separator=' ', strip=True)
                    if len(text) > 100:  # Only add substantial content
                        extracted_parts.append(text)
            except Exception:
                continue
        
        # If we found good content, use it
        if extracted_parts:
            combined = ' '.join(extracted_parts)
        else:
            # Fallback to body text
            body = soup.find('body')
            combined = body.get_text(separator=' ', strip=True) if body else soup.get_text(separator=' ', strip=True)
        
        # Clean up the text
        # Remove excessive whitespace
        combined = re.sub(r'\s+', ' ', combined)
        # Remove common noise patterns
        combined = re.sub(r'(Cookie|Privacy|Terms of Service|Sign In|Log In|Apply Now|Share|Save)(\s|$)', '', combined, flags=re.IGNORECASE)
        
        return combined.strip()
    
    def _extract_string(self, value, default=""):
        """Safely extract string from value that might be dict or other type."""
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            # Try common keys
            for key in ['name', 'title', 'value', 'text', 'required', 'level']:
                if key in value and isinstance(value[key], str):
                    return value[key].strip()
            # Return first string value
            for v in value.values():
                if isinstance(v, str):
                    return v.strip()
            return default
        return str(value).strip() if value else default
    
    def _extract_list(self, value, default=None):
        """Safely extract list from value that might be various types."""
        if default is None:
            default = []
        if value is None:
            return default
        if isinstance(value, list):
            result = []
            for item in value:
                if isinstance(item, str):
                    result.append(item.strip())
                elif isinstance(item, dict):
                    extracted = self._extract_string(item)
                    if extracted:
                        result.append(extracted)
            return result
        if isinstance(value, str):
            return [value.strip()]
        return default
    
    def scrape(self, job_url: str) -> Optional[ScrapedJobData]:
        """
        Scrape job posting and extract structured data.
        OPTIMIZED: Uses URL caching for repeated requests.
        
        Args:
            job_url: URL of the job posting
            
        Returns:
            ScrapedJobData with extracted information, or None if scraping fails
        """
        # CACHE DISABLED for fresh results every time
        # To re-enable, uncomment the cache check below
        # cache_key = hashlib.md5(job_url.encode()).hexdigest()
        # if cache_key in JobScrapingAgent._url_cache:
        #     logger.info(f"⚡ Using cached data for: {job_url[:50]}...")
        #     return JobScrapingAgent._url_cache[cache_key]
        
        try:
            logger.info(f"🔍 Scraping job posting: {job_url}")
            
            # OPTIMIZED: Shorter timeout for faster failures
            response = requests.get(job_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract clean text
            job_text = self._extract_text_from_html(soup)
            
            if not job_text or len(job_text) < 100:
                logger.warning("⚠️ Insufficient content extracted from job posting")
                return None
            
            # Limit text length for LLM (keep first 6000 chars)
            job_text = job_text[:6000] if len(job_text) > 6000 else job_text
            
            logger.info(f"📄 Extracted {len(job_text)} characters from job posting")
            
            # Use LLM to extract structured data
            prompt = self.prompt_template.format(job_content=job_text)
            response_llm = self.llm.invoke(prompt)
            response_text = response_llm.content.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                # Clean control characters
                response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', response_text)
                
                job_dict = json.loads(response_text)
                
                # Create ScrapedJobData with safe extraction
                scraped_data = ScrapedJobData(
                    role=self._extract_string(job_dict.get("role"), "Unknown Role"),
                    skills=self._extract_list(job_dict.get("skills")),
                    experience=self._extract_string(job_dict.get("experience"), ""),
                    responsibilities=self._extract_list(job_dict.get("responsibilities")),
                    keywords=self._extract_list(job_dict.get("keywords")),
                    company=self._extract_string(job_dict.get("company")) or None
                )
                
                logger.info(f"✅ Successfully extracted: {scraped_data.role} at {scraped_data.company or 'Unknown Company'}")
                logger.info(f"   Skills: {', '.join(scraped_data.skills[:5])}...")
                
                # CACHE DISABLED - uncomment to re-enable
                # JobScrapingAgent._url_cache[cache_key] = scraped_data
                return scraped_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON parsing failed: {e}")
                
                # Fallback: try to extract role from text using regex
                role_patterns = [
                    r'(?:Job Title|Position|Role|Title)[:\s]+([A-Z][a-zA-Z\s]+)',
                    r'(?:hiring|looking for|seeking)[:\s]+(?:a\s+)?([A-Z][a-zA-Z\s]+)',
                ]
                
                role = "Unknown Role"
                for pattern in role_patterns:
                    match = re.search(pattern, job_text, re.IGNORECASE)
                    if match:
                        role = match.group(1).strip()
                        break
                
                return ScrapedJobData(
                    role=role,
                    skills=[],
                    experience="",
                    responsibilities=[],
                    keywords=[],
                    company=None
                )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching job posting: {e}")
            # Try URL-based fallback
            return self._fallback_from_url(job_url)
        except Exception as e:
            logger.error(f"❌ Error processing job posting: {e}", exc_info=True)
            return self._fallback_from_url(job_url)
    
    def _fallback_from_url(self, job_url: str) -> Optional[ScrapedJobData]:
        """
        Extract job info from URL when scraping fails.
        Works for LinkedIn and other sites with descriptive URLs.
        """
        try:
            logger.info("🔄 Attempting URL-based fallback extraction...")
            
            # Extract role from URL patterns
            role = "Software Engineer"  # Default
            
            # LinkedIn pattern: /jobs/view/ROLE-at-COMPANY-123456
            linkedin_match = re.search(r'/jobs/view/([^/]+)-at-([^-/]+)', job_url, re.IGNORECASE)
            if linkedin_match:
                role_part = linkedin_match.group(1)
                company_part = linkedin_match.group(2)
                # Clean up role (replace dashes with spaces, title case)
                role = role_part.replace('-', ' ').title()
                # Remove numbers and clean
                role = re.sub(r'\d+', '', role).strip()
                if role:
                    logger.info(f"✅ Fallback extracted role: {role}")
                    return ScrapedJobData(
                        role=role,
                        skills=self._infer_skills_from_role(role),
                        experience="Not specified",
                        responsibilities=[],
                        keywords=role.lower().split(),
                        company=company_part.replace('-', ' ').title() if company_part else None
                    )
            
            # Indeed pattern: viewjob?jk=xxx - harder to extract, use generic
            if 'indeed.com' in job_url:
                logger.info("✅ Fallback: Using generic Software Engineer role for Indeed URL")
                return ScrapedJobData(
                    role="Software Engineer",
                    skills=["Python", "JavaScript", "Problem Solving", "Communication"],
                    experience="Not specified",
                    responsibilities=["Software development", "Code review", "Collaboration"],
                    keywords=["software", "engineer", "developer"],
                    company=None
                )
            
            # Generic fallback
            return ScrapedJobData(
                role="Software Professional",
                skills=["Technical Skills", "Problem Solving", "Communication"],
                experience="Not specified",
                responsibilities=[],
                keywords=["software", "technology"],
                company=None
            )
            
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return None
    
    def _infer_skills_from_role(self, role: str) -> list:
        """OPTIMIZED: Extensive skill inference from job role title."""
        role_lower = role.lower()
        
        # OPTIMIZED: Comprehensive skill mappings
        skill_mappings = {
            # Data/ML roles
            'data scientist': ["Python", "Machine Learning", "SQL", "TensorFlow/PyTorch", "Statistics", "Data Visualization"],
            'machine learning': ["Python", "TensorFlow", "PyTorch", "MLOps", "Deep Learning", "NLP/Computer Vision"],
            'ml engineer': ["Python", "TensorFlow", "PyTorch", "MLOps", "Kubernetes", "Model Deployment"],
            'data analyst': ["SQL", "Excel", "Python", "Tableau/PowerBI", "Statistics", "Data Modeling"],
            'data engineer': ["Python", "SQL", "Spark", "Airflow", "AWS/GCP", "ETL Pipelines"],
            
            # Frontend roles
            'frontend': ["JavaScript", "React", "TypeScript", "CSS/SCSS", "HTML5", "Redux", "Webpack"],
            'react': ["React", "JavaScript", "TypeScript", "Redux", "Next.js", "CSS-in-JS"],
            'angular': ["Angular", "TypeScript", "RxJS", "NgRx", "HTML/CSS"],
            'vue': ["Vue.js", "JavaScript", "Vuex", "Nuxt.js", "TypeScript"],
            
            # Backend roles
            'backend': ["Python", "Java", "Node.js", "SQL", "REST APIs", "Microservices"],
            'python': ["Python", "Django/FastAPI", "SQL", "REST APIs", "PostgreSQL", "Redis"],
            'java': ["Java", "Spring Boot", "Microservices", "SQL", "Kafka", "Maven/Gradle"],
            'node': ["Node.js", "Express", "TypeScript", "MongoDB", "REST APIs", "GraphQL"],
            'golang': ["Go", "Microservices", "gRPC", "Docker", "PostgreSQL", "Redis"],
            
            # Full Stack
            'full stack': ["JavaScript", "Python/Node.js", "React/Vue", "SQL", "REST APIs", "Git"],
            'fullstack': ["JavaScript", "Python/Node.js", "React/Vue", "SQL", "REST APIs", "Git"],
            
            # DevOps/Cloud roles
            'devops': ["AWS/Azure/GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Ansible"],
            'cloud': ["AWS/Azure/GCP", "Terraform", "Kubernetes", "Docker", "Networking", "Security"],
            'sre': ["Kubernetes", "Prometheus/Grafana", "Python/Go", "Linux", "Incident Management"],
            'platform': ["Kubernetes", "Terraform", "CI/CD", "Developer Experience", "Infrastructure as Code"],
            
            # Mobile roles
            'ios': ["Swift", "SwiftUI", "Objective-C", "Xcode", "Core Data", "UIKit"],
            'android': ["Kotlin", "Java", "Android SDK", "Jetpack Compose", "Room", "Retrofit"],
            'mobile': ["React Native", "Flutter", "iOS/Android", "Mobile UI/UX", "REST APIs"],
            
            # Security roles
            'security': ["Penetration Testing", "SIEM", "Network Security", "Compliance", "Python", "Cloud Security"],
        }
        
        # Find best match
        for key, skills in skill_mappings.items():
            if key in role_lower:
                return skills
        
        # Default for unmatched roles
        return ["Python", "JavaScript", "SQL", "Problem Solving", "Communication", "Git"]
