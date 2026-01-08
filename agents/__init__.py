"""
Agents package for Cold Outreach AI Agent.
"""

import os

from agents.planner_agent import PlannerAgent
from agents.persona_agent import PersonaAnalyzerAgent
from agents.generation_agent import EmailGenerationAgent
from agents.evaluation_agent import EvaluationAgent
from agents.scraper_agent import JobScrapingAgent

# Import appropriate agents based on LITE_MODE setting
USE_LITE_MODE = os.environ.get("LITE_MODE", "true").lower() == "true"

if USE_LITE_MODE:
    from agents.retrieval_agent_lite import TemplateRetrievalAgent
    from agents.portfolio_agent_lite import PortfolioRetrievalAgent
else:
    from agents.retrieval_agent import TemplateRetrievalAgent
    from agents.portfolio_agent import PortfolioRetrievalAgent
    "TemplateRetrievalAgent",
    "EmailGenerationAgent",
    "EvaluationAgent",
    "PortfolioRetrievalAgent",
    "JobScrapingAgent"
]

