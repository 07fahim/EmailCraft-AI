"""
FastAPI backend for Cold Outreach AI Agent.
Provides REST API endpoints for the agent system.
"""

import os
import logging
import math
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Any

from models.schemas import AgentRequest
from agents.planner_agent import PlannerAgent
from database.db_manager import get_db


def sanitize_floats(obj: Any) -> Any:
    """Recursively sanitize float values (inf, nan) to be JSON compliant."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0  # Replace invalid floats with 0
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_floats(item) for item in obj]
    return obj


class SafeJSONResponse(JSONResponse):
    """Custom JSON response that handles inf/nan values."""
    def render(self, content: Any) -> bytes:
        sanitized = sanitize_floats(content)
        return json.dumps(
            sanitized,
            ensure_ascii=False,
            allow_nan=False,  # This will raise error if nan/inf still present
            separators=(",", ":")
        ).encode("utf-8")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EmailCraft AI API",
    description="Multi-agent AI system for generating high-conversion B2B outreach emails",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize planner agent
planner = PlannerAgent()


@app.on_event("startup")
async def startup_event():
    """Warm up the system on startup for faster first requests."""
    logger.info("🚀 Starting Cold Outreach AI Agent...")
    try:
        # Warm up LLM connection
        from utils.groq_client import GroqClient
        client = GroqClient()
        client.warm_up()
        logger.info("✅ System ready - first request will be fast!")
    except Exception as e:
        logger.warning(f"Warm-up skipped: {e}")


class EmailRequest(BaseModel):
    """API request model with two mutually exclusive input modes."""
    job_url: Optional[str] = Field(default=None, description="Job posting URL (optional)")
    role: Optional[str] = Field(default=None, description="Target role (required if no job_url)")
    industry: Optional[str] = Field(default=None, description="Target industry (required if no job_url)")
    tone: Optional[str] = Field(default="professional", description="Email tone")
    company_name: Optional[str] = None
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = Field(default="Alex", description="Your name for email signature")
    sender_company: Optional[str] = Field(default="TechSolutions Inc.", description="Your company name")
    sender_services: Optional[str] = Field(default="software development and consulting services", description="Your services")


class EmailResponse(BaseModel):
    """API response model."""
    success: bool
    data: dict
    message: Optional[str] = None


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "EmailCraft AI API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/history")
async def get_history():
    """Get email generation history."""
    try:
        db = get_db()
        emails = db.get_all_emails(limit=100)
        return emails
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics")
async def get_analytics():
    """Get analytics dashboard data."""
    try:
        db = get_db()
        analytics = db.get_analytics()
        
        # Get recent emails for activity feed
        recent_emails = db.get_all_emails(limit=10)
        recent_activity = [
            {
                "company": email.get("company_name", "Unknown"),
                "role": email.get("role", "Unknown"),
                "score": email.get("final_score", 0),
                "created_at": email.get("timestamp", "")
            }
            for email in recent_emails
        ]
        
        # Calculate unique companies
        all_emails = db.get_all_emails(limit=1000)
        unique_companies = len(set(
            email.get("company_name", "") for email in all_emails 
            if email.get("company_name")
        ))
        
        # Calculate score distribution
        score_buckets = {"0-5": 0, "5-6": 0, "6-7": 0, "7-8": 0, "8-9": 0, "9-10": 0}
        for email in all_emails:
            score = email.get("final_score", 0) or 0
            if score < 5:
                score_buckets["0-5"] += 1
            elif score < 6:
                score_buckets["5-6"] += 1
            elif score < 7:
                score_buckets["6-7"] += 1
            elif score < 8:
                score_buckets["7-8"] += 1
            elif score < 9:
                score_buckets["8-9"] += 1
            else:
                score_buckets["9-10"] += 1
        
        score_distribution = [{"range": k, "count": v} for k, v in score_buckets.items() if v > 0]
        
        # Format for frontend
        return {
            "total_emails": analytics.get("total_emails", 0),
            "avg_score": analytics.get("average_score", 0),
            "unique_companies": unique_companies,
            "high_score_count": analytics.get("high_quality_count", 0),
            "roles_distribution": [
                {"role": role, "count": count} 
                for role, count in analytics.get("top_roles", [])
            ],
            "score_distribution": score_distribution,
            "recent_activity": recent_activity
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/template-performance")
async def get_template_performance():
    """Get template performance ranking."""
    try:
        db = get_db()
        performance = db.get_template_performance()
        return performance
    except Exception as e:
        logger.error(f"Error fetching template performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate_email(request: EmailRequest):
    """
    Generate a cold email using the multi-agent system.
    
    Two input modes:
    1. Job URL Mode: job_url + product
    2. Structured Mode: role + industry + product
    """
    try:
        # Validate input mode
        if not request.job_url:
            if not request.role or not request.industry:
                raise HTTPException(
                    status_code=400,
                    detail="Either provide job_url OR (role + industry)"
                )
        
        # Convert to AgentRequest
        agent_request = AgentRequest(
            role=request.role,
            industry=request.industry,
            tone=request.tone,
            company_name=request.company_name,
            recipient_name=request.recipient_name,
            job_url=request.job_url,
            sender_name=request.sender_name,
            sender_company=request.sender_company,
            sender_services=request.sender_services
        )
        
        # Execute agent pipeline
        logger.info(f"Processing request for: {request.role or 'job URL'}")
        result = planner.execute_with_metadata(agent_request)
        
        # Sanitize result to remove inf/nan values and return with SafeJSONResponse
        sanitized_result = sanitize_floats(result)
        
        # Format response for new frontend
        # The planner returns "final_email" but frontend expects "email"
        final_email = sanitized_result.get("final_email", {})
        evaluation_details = sanitized_result.get("evaluation_details", {})
        portfolio_items = sanitized_result.get("portfolio_items_used", [])
        
        # Debug: log portfolio items
        logger.info(f"📦 Portfolio items in response: {len(portfolio_items)}")
        for idx, item in enumerate(portfolio_items):
            logger.info(f"   Item {idx+1}: {item}")
        
        response_data = {
            "email": {
                "subject_line": final_email.get("subject_line", ""),
                "body": final_email.get("body", ""),
                "cta": final_email.get("cta", "")
            },
            "evaluation": {
                "overall_score": sanitized_result.get("final_score", 0),
                "clarity_score": evaluation_details.get("clarity_score", 0),
                "tone_alignment_score": evaluation_details.get("tone_alignment_score", 0),
                "length_score": evaluation_details.get("length_score", 0),
                "personalization_score": evaluation_details.get("personalization_score", 0),
                "spam_risk_score": evaluation_details.get("spam_risk_score", 5),
                "strengths": evaluation_details.get("strengths", []),
                "issues": evaluation_details.get("issues", [])
            },
            "alternative_subject_lines": sanitized_result.get("alternative_subject_lines", []),
            "optimization_applied": sanitized_result.get("optimization_applied", False),
            "initial_score": sanitized_result.get("initial_score", 0),
            "portfolio_items_used": portfolio_items,
            "persona_snapshot": sanitized_result.get("persona_snapshot", {}),
            "scraped_job_data": sanitized_result.get("scraped_job_data", None)
        }
        
        return SafeJSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating email: {str(e)}"
        )


# Keep old endpoint for Streamlit compatibility
@app.post("/generate-email")
async def generate_email_legacy(request: EmailRequest):
    """Legacy endpoint for Streamlit app compatibility."""
    try:
        if not request.job_url:
            if not request.role or not request.industry:
                raise HTTPException(
                    status_code=400,
                    detail="Either provide job_url OR (role + industry)"
                )
        
        agent_request = AgentRequest(
            role=request.role,
            industry=request.industry,
            tone=request.tone,
            company_name=request.company_name,
            recipient_name=request.recipient_name,
            job_url=request.job_url,
            sender_name=request.sender_name,
            sender_company=request.sender_company,
            sender_services=request.sender_services
        )
        
        logger.info(f"Processing request (legacy) for: {request.role or 'job URL'}")
        result = planner.execute_with_metadata(agent_request)
        sanitized_result = sanitize_floats(result)
        
        return SafeJSONResponse(content={
            "success": True,
            "data": sanitized_result,
            "message": "Email generated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating email: {str(e)}")


# Serve static frontend files
FRONTEND_DIR = Path(__file__).parent / "frontend"

if FRONTEND_DIR.exists():
    @app.get("/")
    async def serve_frontend():
        """Serve the main frontend page."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))
    
    @app.get("/{filename:path}")
    async def serve_static_files(filename: str):
        """Serve static files (CSS, JS, etc.)."""
        file_path = FRONTEND_DIR / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Return index.html for SPA routing
        return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)