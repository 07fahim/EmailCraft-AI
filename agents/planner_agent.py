"""
Planner Agent - WITH DATABASE INTEGRATION
Orchestrates the multi-agent pipeline for email generation.
OPTIMIZED: Faster execution, better error handling, execution tracking.
"""

import os
import logging
import time
from typing import Dict, Any, Optional

from models.schemas import (
    AgentRequest,
    PersonaInput,
    EmailGenerationInput,
    ScrapedJobData,
    PortfolioItem
)
from agents.persona_agent import PersonaAnalyzerAgent
from agents.generation_agent import EmailGenerationAgent
from agents.evaluation_agent import EvaluationAgent
from agents.scraper_agent import JobScrapingAgent

# Use LITE mode for memory-constrained environments (free tier hosting)
# Set LITE_MODE=true in environment to use lightweight keyword matching
USE_LITE_MODE = os.environ.get("LITE_MODE", "true").lower() == "true"

if USE_LITE_MODE:
    from agents.retrieval_agent_lite import TemplateRetrievalAgent
    from agents.portfolio_agent_lite import PortfolioRetrievalAgent
    logging.info("🪶 Using LITE mode (keyword matching) - memory efficient")
else:
    from agents.retrieval_agent import TemplateRetrievalAgent
    from agents.portfolio_agent import PortfolioRetrievalAgent
    logging.info("🔧 Using FULL mode (ChromaDB embeddings)")

# Import database manager
from database.db_manager import get_db

logger = logging.getLogger(__name__)


class PlannerAgent:
    """Planner Agent with Analytics Tracking. OPTIMIZED for speed and accuracy."""
    
    def __init__(self):
        """Initialize all sub-agents."""
        self.scraper_agent = JobScrapingAgent()  # Dedicated scraping agent
        self.persona_agent = PersonaAnalyzerAgent()
        self.retrieval_agent = TemplateRetrievalAgent()
        self.portfolio_agent = PortfolioRetrievalAgent()
        self.generation_agent = EmailGenerationAgent()
        self.evaluation_agent = EvaluationAgent()
        
        # Initialize database
        self.db = get_db()
        
        # OPTIMIZED: Track execution times
        self._last_execution_time = 0
    
    def execute(self, request: AgentRequest) -> Dict[str, Any]:
        """Execute pipeline WITH database tracking. OPTIMIZED with timing."""
        start_time = time.time()
        
        # Step 0: Determine input mode
        scraped_job_data: Optional[ScrapedJobData] = None
        
        if request.job_url:
            logger.info("🔍 Step 0: Scraping job posting...")
            scraped_job_data = self.scraper_agent.scrape(request.job_url)
            
            if scraped_job_data:
                logger.info(f"✅ Extracted role: {scraped_job_data.role}")
                logger.info(f"✅ Company: {scraped_job_data.company}")
                logger.info(f"✅ Skills: {', '.join(scraped_job_data.skills[:5])}")
                role = scraped_job_data.role
                industry = scraped_job_data.company or request.industry or "Technology"
                if scraped_job_data.company and not request.company_name:
                    request.company_name = scraped_job_data.company
            else:
                logger.warning("⚠️ Job scraping failed")
                if not request.role or not request.industry:
                    raise ValueError("Job scraping failed and no fallback provided. Please provide role + industry manually.")
                role = request.role
                industry = request.industry
        else:
            if not request.role or not request.industry:
                raise ValueError("Either job_url OR (role + industry) required")
            role = request.role
            industry = request.industry
            logger.info(f"Using structured input: {role} in {industry}")
        
        # Step 1: Persona Analysis
        logger.info("🎯 Step 1: Analyzing persona...")
        persona_input = PersonaInput(
            role=role,
            industry=industry,
            tone=request.tone or "professional",
            scraped_job_data=scraped_job_data
        )
        persona_output = self.persona_agent.analyze(persona_input)
        
        # Step 2: Template Retrieval
        logger.info("📚 Step 2: Retrieving email templates...")
        retrieved_templates = self.retrieval_agent.retrieve(
            persona=persona_output,
            product=role,
            industry=industry
        )
        
        # Step 3: Portfolio Retrieval
        logger.info("💼 Step 3: Retrieving portfolio items...")
        portfolio_items = self.portfolio_agent.retrieve(
            persona=persona_output,
            scraped_job_data=scraped_job_data,
            product=role,
            industry=industry
        )
        logger.info(f"✅ Retrieved {len(portfolio_items)} portfolio items")
        if portfolio_items:
            for idx, item in enumerate(portfolio_items):
                logger.info(f"   Portfolio {idx+1}: {item.get('title', 'N/A')} - {item.get('link', 'N/A')}")
        
        portfolio_objs = [
            PortfolioItem(
                title=item["title"],
                tech_stack=item["tech_stack"],
                description=item["description"],
                outcomes=item["outcomes"],
                link=item["link"],
                similarity_score=item["similarity_score"]
            )
            for item in portfolio_items
        ]
        
        # Step 4: Email Generation
        logger.info("✍️ Step 4: Generating email...")
        company_name = request.company_name
        if scraped_job_data and scraped_job_data.company and not company_name:
            company_name = scraped_job_data.company
        
        generation_input = EmailGenerationInput(
            persona=persona_output,
            templates=retrieved_templates,
            portfolio_items=portfolio_objs,
            company_name=company_name,
            recipient_name=request.recipient_name,
            sender_name=request.sender_name,
            sender_company=request.sender_company,
            sender_services=request.sender_services,
            scraped_job_data=scraped_job_data
        )
        email_draft = self.generation_agent.generate(generation_input)
        
        # Step 5: Evaluation & Optimization (with job context)
        logger.info("🎯 Step 5: Evaluating and optimizing...")
        
        # Extract job role for context-aware evaluation
        job_role_for_eval = role  # Default to extracted role
        if scraped_job_data and scraped_job_data.role:
            job_role_for_eval = scraped_job_data.role
        
        optimized_email = self.evaluation_agent.evaluate_and_optimize(
            email_draft=email_draft,
            persona=persona_output,
            original_templates=retrieved_templates,
            job_role=job_role_for_eval,
            target_company=company_name or "the company"
        )
        
        # Build result
        optimized_dict = optimized_email.to_dict()
        
        result = {
            **optimized_dict,
            "persona_snapshot": persona_output.to_dict(),
            "portfolio_items_used": portfolio_items,
            "agent_execution_summary": {
                "job_scraping_used": scraped_job_data is not None,
                "optimization_applied": optimized_email.optimization_applied,
                "templates_used": len(retrieved_templates),
                "portfolio_items_retrieved": len(portfolio_items)
            }
        }
        
        if scraped_job_data:
            result["scraped_job_data"] = scraped_job_data.to_dict()
        
        # ✅ NEW: Save to database
        try:
            email_data = {
                "job_url": request.job_url,
                "role": role,
                "industry": industry,
                "company_name": company_name,
                "recipient_name": request.recipient_name,
                "subject_line": optimized_email.email.subject_line,
                "body": optimized_email.email.body,
                "cta": optimized_email.email.cta,
                "initial_score": optimized_email.initial_score,
                "final_score": optimized_email.evaluation.overall_score,
                "optimization_applied": optimized_email.optimization_applied,
                "clarity_score": optimized_email.evaluation.clarity_score,
                "tone_score": optimized_email.evaluation.tone_alignment_score,
                "length_score": optimized_email.evaluation.length_score,
                "personalization_score": optimized_email.evaluation.personalization_score,
                "spam_risk_score": optimized_email.evaluation.spam_risk_score,
                "templates_used": [t.template.id for t in retrieved_templates],
                "portfolio_items_used": [item["title"] for item in portfolio_items],
                "sender_name": request.sender_name,
                "sender_company": request.sender_company,
                "strengths": optimized_email.evaluation.strengths,
                "issues": optimized_email.evaluation.issues,
                "alternative_subject_lines": optimized_email.alternative_subject_lines
            }
            
            logger.info(f"📝 Email data to save - Strengths: {email_data.get('strengths')}, Issues: {email_data.get('issues')}, Alt Subjects: {email_data.get('alternative_subject_lines')}")
            
            email_id = self.db.save_email(email_data)
            result["email_id"] = email_id  # Add email ID to result
            
            # ✅ NEW: Track template performance
            for template in retrieved_templates:
                self.db.save_template_usage(
                    template_id=template.template.id,
                    template_title=template.template.title,
                    email_score=optimized_email.evaluation.overall_score,
                    email_generation_id=email_id
                )
            
            logger.info(f"✅ Saved email to database (ID: {email_id})")
            
        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            # Don't fail the whole request if database save fails
        
        # OPTIMIZED: Track and log execution time
        self._last_execution_time = time.time() - start_time
        logger.info(f"⏱️ Total execution time: {self._last_execution_time:.2f}s")
        result["execution_time_seconds"] = round(self._last_execution_time, 2)
        
        return result
    
    def execute_with_metadata(self, request: AgentRequest) -> Dict[str, Any]:
        """Execute with detailed metadata."""
        return self.execute(request)