"""
Models package - Pydantic schemas for data exchange.
"""

from models.schemas import (
    AgentRequest,
    ScrapedJobData,
    PersonaInput,
    PersonaOutput,
    EmailTemplate,
    RetrievedTemplate,
    EmailGenerationInput,
    EmailDraft,
    EvaluationMetrics,
    OptimizedEmail
)

__all__ = [
    "AgentRequest",
    "ScrapedJobData",
    "PersonaInput",
    "PersonaOutput",
    "EmailTemplate",
    "RetrievedTemplate",
    "EmailGenerationInput",
    "EmailDraft",
    "EvaluationMetrics",
    "OptimizedEmail"
]

