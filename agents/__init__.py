"""
Agents package for Cold Outreach AI Agent.
"""

import os

from agents.planner_agent import PlannerAgent
from agents.persona_agent import PersonaAnalyzerAgent
from agents.generation_agent import EmailGenerationAgent
from agents.evaluation_agent import EvaluationAgent
from agents.scraper_agent import JobScrapingAgent

# Import appropriate agents based on VECTOR_MODE setting
VECTOR_MODE = os.environ.get("VECTOR_MODE", "LITE").upper()

if VECTOR_MODE == "PINECONE" and os.environ.get("PINECONE_API_KEY"):
    from agents.retrieval_agent_pinecone import TemplateRetrievalAgent
    from agents.portfolio_agent_pinecone import PortfolioRetrievalAgent
elif VECTOR_MODE == "FULL":
    from agents.retrieval_agent import TemplateRetrievalAgent
    from agents.portfolio_agent import PortfolioRetrievalAgent
else:
    from agents.retrieval_agent_lite import TemplateRetrievalAgent
    from agents.portfolio_agent_lite import PortfolioRetrievalAgent

__all__ = [
    "PlannerAgent",
    "PersonaAnalyzerAgent",
    "TemplateRetrievalAgent",
    "EmailGenerationAgent",
    "EvaluationAgent",
    "PortfolioRetrievalAgent",
    "JobScrapingAgent",
]
