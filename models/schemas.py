"""
Pydantic models - OPTIMIZED VERSION
Product field removed - inferred from job posting or role
"""

import math
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


def clamp_score(v: float) -> float:
    """Clamp score to valid range and handle inf/nan."""
    if v != v or math.isinf(v):  # NaN or inf check
        return 7.0
    return max(0.0, min(10.0, v))


class ScrapedJobData(BaseModel):
    """Output from job scraping."""
    role: str
    skills: List[str] = Field(default_factory=list)
    experience: str = ""
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    company: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "skills": self.skills,
            "experience": self.experience,
            "responsibilities": self.responsibilities,
            "keywords": self.keywords,
            "company": self.company
        }


class PersonaInput(BaseModel):
    """Input for Persona Analyzer Agent."""
    role: Optional[str] = None
    industry: Optional[str] = None
    scraped_job_data: Optional[ScrapedJobData] = None
    tone: str = "professional"


class PersonaOutput(BaseModel):
    """Output from Persona Analyzer Agent."""
    pain_points: List[str]
    decision_drivers: List[str]
    communication_style: str
    tone: str
    value_focus: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pain_points": self.pain_points,
            "decision_drivers": self.decision_drivers,
            "communication_style": self.communication_style,
            "tone": self.tone,
            "value_focus": self.value_focus
        }


class EmailTemplate(BaseModel):
    """Email template structure for RAG."""
    id: str
    title: str
    industry: str
    use_case: str
    subject_line: str
    body: str
    cta: str
    performance_score: float = 0.0


class RetrievedTemplate(BaseModel):
    """Template retrieved from vector store."""
    template: EmailTemplate
    similarity_score: float


class PortfolioItem(BaseModel):
    """Portfolio/case study item."""
    title: str
    tech_stack: str
    description: str
    outcomes: str
    link: str
    similarity_score: float = 0.0


class EmailGenerationInput(BaseModel):
    """Input for Email Generation Agent."""
    persona: PersonaOutput
    templates: List[RetrievedTemplate]
    portfolio_items: List[PortfolioItem]
    company_name: Optional[str] = None
    recipient_name: Optional[str] = None
    sender_name: str = "Alex"
    sender_company: str = "TechSolutions Inc."
    sender_services: str = "software development and consulting services"
    scraped_job_data: Optional[ScrapedJobData] = None


class EmailDraft(BaseModel):
    """Generated email draft."""
    subject_line: str
    body: str
    cta: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_line": self.subject_line,
            "body": self.body,
            "cta": self.cta
        }


class EvaluationMetrics(BaseModel):
    """Evaluation metrics for email quality."""
    clarity_score: float = Field(default=7.0, ge=0.0, le=10.0)
    tone_alignment_score: float = Field(default=7.0, ge=0.0, le=10.0)
    length_score: float = Field(default=7.0, ge=0.0, le=10.0)
    spam_risk_score: float = Field(default=5.0, ge=0.0, le=10.0)
    personalization_score: float = Field(default=7.0, ge=0.0, le=10.0)
    overall_score: float = Field(default=7.0, ge=0.0, le=10.0)
    issues: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    
    @field_validator('clarity_score', 'tone_alignment_score', 'length_score', 
                     'spam_risk_score', 'personalization_score', 'overall_score', mode='before')
    @classmethod
    def sanitize_score(cls, v):
        """Sanitize scores to valid range, handling inf/nan."""
        try:
            f = float(v) if v is not None else 7.0
            if f != f or math.isinf(f):  # NaN or inf
                return 7.0
            return max(0.0, min(10.0, f))
        except (ValueError, TypeError):
            return 7.0


class OptimizedEmail(BaseModel):
    """Final optimized email output."""
    email: EmailDraft
    alternative_subject_lines: List[str]
    evaluation: EvaluationMetrics
    optimization_applied: bool = False
    initial_score: Optional[float] = None
    improvements_summary: List[str] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_email": self.email.to_dict(),
            "final_score": self.evaluation.overall_score,
            "initial_score": self.initial_score or self.evaluation.overall_score,
            "optimization_applied": self.optimization_applied,
            "improvements_summary": self.improvements_summary,
            "alternative_subject_lines": self.alternative_subject_lines,
            "evaluation_details": {
                "clarity_score": self.evaluation.clarity_score,
                "tone_alignment_score": self.evaluation.tone_alignment_score,
                "length_score": self.evaluation.length_score,
                "spam_risk_score": self.evaluation.spam_risk_score,
                "personalization_score": self.evaluation.personalization_score,
                "issues": self.evaluation.issues,
                "strengths": self.evaluation.strengths
            }
        }


class AgentRequest(BaseModel):
    """
    Complete request for the agent system.
    
    Two input modes:
    1. Job URL ONLY: job_url
    2. Structured: role + industry + company_name
    
    Product/service is INFERRED from job requirements or role.
    """
    # Job URL Mode
    job_url: Optional[str] = Field(
        default=None, 
        description="Job posting URL - system infers what service to offer"
    )
    
    # Structured Input Mode (if no job_url)
    role: Optional[str] = Field(
        default=None, 
        description="Target role (required if no job_url)"
    )
    industry: Optional[str] = Field(
        default=None, 
        description="Target industry (required if no job_url)"
    )
    company_name: Optional[str] = Field(
        default=None, 
        description="Target company name"
    )
    
    # Optional personalization
    recipient_name: Optional[str] = None
    tone: Optional[str] = "professional"
    
    # Your business identity (who you are)
    sender_name: str = "Alex"
    sender_company: str = "TechSolutions Inc."
    sender_services: str = "software development and consulting services"