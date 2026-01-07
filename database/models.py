"""
Database Models - Defines what data we store.

Think of this like creating Excel sheets:
- EmailGeneration sheet: stores each email we generate
- TemplateUsage sheet: tracks which templates are used
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class EmailGeneration(Base):
    """
    Stores every email we generate.
    Like an Excel row with these columns:
    - id, timestamp, recipient info, email content, scores, etc.
    """
    __tablename__ = "email_generations"
    
    # Primary key (unique ID for each email)
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # When was it generated?
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Input data
    job_url = Column(String, nullable=True)
    role = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    recipient_name = Column(String, nullable=True)
    
    # Generated email
    subject_line = Column(Text)
    body = Column(Text)
    cta = Column(String)
    
    # Quality scores
    initial_score = Column(Float)
    final_score = Column(Float)
    optimization_applied = Column(Boolean, default=False)
    
    # Detailed evaluation metrics (5 scores)
    clarity_score = Column(Float, nullable=True)
    tone_score = Column(Float, nullable=True)
    length_score = Column(Float, nullable=True)
    personalization_score = Column(Float, nullable=True)
    spam_risk_score = Column(Float, nullable=True)
    
    # Which templates were used?
    templates_used = Column(String)  # Store as comma-separated IDs
    
    # Which portfolio items matched?
    portfolio_items_used = Column(String)  # Store as comma-separated
    
    # Evaluation feedback (NEW)
    strengths = Column(Text, nullable=True)  # Store as JSON array
    issues = Column(Text, nullable=True)  # Store as JSON array
    alternative_subject_lines = Column(Text, nullable=True)  # Store as JSON array
    
    # Metadata
    sender_name = Column(String)
    sender_company = Column(String)
    
    def to_dict(self):
        """Convert database row to Python dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "job_url": self.job_url,
            "role": self.role,
            "industry": self.industry,
            "company_name": self.company_name,
            "recipient_name": self.recipient_name,
            "subject_line": self.subject_line,
            "body": self.body,
            "cta": self.cta,
            "initial_score": self.initial_score,
            "final_score": self.final_score,
            "optimization_applied": self.optimization_applied,
            "clarity_score": self.clarity_score,
            "tone_score": self.tone_score,
            "length_score": self.length_score,
            "personalization_score": self.personalization_score,
            "spam_risk_score": self.spam_risk_score,
            "templates_used": self.templates_used,
            "portfolio_items_used": self.portfolio_items_used,
            "strengths": self.strengths,
            "issues": self.issues,
            "alternative_subject_lines": self.alternative_subject_lines,
            "sender_name": self.sender_name,
            "sender_company": self.sender_company
        }


class TemplateUsage(Base):
    """
    Tracks template performance.
    Each time a template is used, we record its score.
    """
    __tablename__ = "template_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Which template?
    template_id = Column(String, nullable=False)
    template_title = Column(String)
    
    # What score did the email get?
    email_score = Column(Float)
    
    # Link to the email generation
    email_generation_id = Column(Integer)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "template_id": self.template_id,
            "template_title": self.template_title,
            "email_score": self.email_score,
            "email_generation_id": self.email_generation_id
        }