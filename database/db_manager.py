"""
Database Manager - Simple functions to save/retrieve data.

For beginners: Think of this as helper functions that let you:
- save_email() - Save an email to database
- get_analytics() - Get statistics
- get_all_emails() - Get email history

No need to understand SQL - just use these functions!
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from database.models import Base, EmailGeneration, TemplateUsage

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Simple database manager for beginners.
    
    Usage:
        db = DatabaseManager()
        db.save_email(email_data)
        analytics = db.get_analytics()
    """
    
    def __init__(self, db_path: str = "analytics.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (created automatically)
        """
        # Create database engine (connects to SQLite file)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        
        # Create all tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create session factory (for database operations)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        logger.info(f"✅ Database initialized: {db_path}")
    
    def save_email(self, email_data: Dict[str, Any]) -> int:
        """
        Save a generated email to database.
        
        Args:
            email_data: Dictionary with email details
            
        Returns:
            ID of saved email
        
        Example:
            email_id = db.save_email({
                "job_url": "https://...",
                "subject_line": "...",
                "body": "...",
                "final_score": 8.7
            })
        """
        try:
            # Create database record
            email = EmailGeneration(
                job_url=email_data.get("job_url"),
                role=email_data.get("role"),
                industry=email_data.get("industry"),
                company_name=email_data.get("company_name"),
                recipient_name=email_data.get("recipient_name"),
                subject_line=email_data.get("subject_line"),
                body=email_data.get("body"),
                cta=email_data.get("cta"),
                initial_score=email_data.get("initial_score"),
                final_score=email_data.get("final_score"),
                optimization_applied=email_data.get("optimization_applied", False),
                clarity_score=email_data.get("clarity_score"),
                tone_score=email_data.get("tone_score"),
                length_score=email_data.get("length_score"),
                personalization_score=email_data.get("personalization_score"),
                spam_risk_score=email_data.get("spam_risk_score"),
                templates_used=",".join(email_data.get("templates_used", [])),
                portfolio_items_used=",".join(email_data.get("portfolio_items_used", [])),
                strengths=json.dumps(email_data.get("strengths", [])),  # Store as JSON string
                issues=json.dumps(email_data.get("issues", [])),  # Store as JSON string
                alternative_subject_lines=json.dumps(email_data.get("alternative_subject_lines", [])),  # Store as JSON string
                sender_name=email_data.get("sender_name"),
                sender_company=email_data.get("sender_company")
            )
            
            logger.info(f"💾 Saving to DB - Strengths: {email_data.get('strengths')}, Issues: {email_data.get('issues')}, Alt Subjects: {email_data.get('alternative_subject_lines')}")
            
            # Save to database
            self.session.add(email)
            self.session.commit()
            
            logger.info(f"✅ Saved email to database (ID: {email.id})")
            return email.id
            
        except Exception as e:
            logger.error(f"❌ Error saving email: {e}")
            self.session.rollback()
            return -1
    
    def save_template_usage(self, template_id: str, template_title: str, 
                           email_score: float, email_generation_id: int):
        """
        Track template usage and performance.
        
        Example:
            db.save_template_usage("template_1", "Hiring Alternative", 8.7, 123)
        """
        try:
            usage = TemplateUsage(
                template_id=template_id,
                template_title=template_title,
                email_score=email_score,
                email_generation_id=email_generation_id
            )
            
            self.session.add(usage)
            self.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Error saving template usage: {e}")
            self.session.rollback()
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get analytics dashboard data.
        
        Returns:
            Dictionary with all analytics metrics
        
        Example:
            analytics = db.get_analytics()
            print(f"Total emails: {analytics['total_emails']}")
            print(f"Average score: {analytics['average_score']}")
        """
        try:
            # Total emails generated
            total_emails = self.session.query(EmailGeneration).count()
            
            # Average quality score
            avg_score = self.session.query(
                func.avg(EmailGeneration.final_score)
            ).scalar() or 0.0
            
            # Success rate (score >= 8.0)
            high_quality_count = self.session.query(EmailGeneration).filter(
                EmailGeneration.final_score >= 8.0
            ).count()
            success_rate = (high_quality_count / total_emails * 100) if total_emails > 0 else 0
            
            # Optimization rate
            optimized_count = self.session.query(EmailGeneration).filter(
                EmailGeneration.optimization_applied == True
            ).count()
            optimization_rate = (optimized_count / total_emails * 100) if total_emails > 0 else 0
            
            # Most common roles
            top_roles = self.session.query(
                EmailGeneration.role,
                func.count(EmailGeneration.role).label('count')
            ).filter(
                EmailGeneration.role.isnot(None)
            ).group_by(
                EmailGeneration.role
            ).order_by(
                desc('count')
            ).limit(5).all()
            
            # Recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = self.session.query(EmailGeneration).filter(
                EmailGeneration.timestamp >= seven_days_ago
            ).count()
            
            return {
                "total_emails": total_emails,
                "average_score": round(avg_score, 2),
                "success_rate": round(success_rate, 1),
                "optimization_rate": round(optimization_rate, 1),
                "top_roles": [(role, count) for role, count in top_roles],
                "recent_activity_7days": recent_count,
                "high_quality_count": high_quality_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting analytics: {e}")
            return {
                "total_emails": 0,
                "average_score": 0.0,
                "success_rate": 0.0,
                "optimization_rate": 0.0,
                "top_roles": [],
                "recent_activity_7days": 0,
                "high_quality_count": 0
            }
    
    def get_template_performance(self) -> List[Dict[str, Any]]:
        """
        Get performance statistics for each template.
        
        Returns:
            List of templates with their average scores and usage count
        """
        try:
            results = self.session.query(
                TemplateUsage.template_id,
                TemplateUsage.template_title,
                func.avg(TemplateUsage.email_score).label('avg_score'),
                func.count(TemplateUsage.id).label('usage_count')
            ).group_by(
                TemplateUsage.template_id,
                TemplateUsage.template_title
            ).order_by(
                desc('avg_score')
            ).all()
            
            return [
                {
                    "template_id": r.template_id,
                    "template_title": r.template_title,
                    "avg_score": round(r.avg_score, 2),
                    "usage_count": r.usage_count
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting template performance: {e}")
            return []
    
    def get_all_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all generated emails (for export/history).
        
        Args:
            limit: Maximum number of emails to return
            
        Returns:
            List of email dictionaries
        """
        try:
            emails = self.session.query(EmailGeneration).order_by(
                desc(EmailGeneration.timestamp)
            ).limit(limit).all()
            
            return [email.to_dict() for email in emails]
            
        except Exception as e:
            logger.error(f"❌ Error getting emails: {e}")
            return []
    
    def get_email_by_id(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific email by ID."""
        try:
            email = self.session.query(EmailGeneration).filter(
                EmailGeneration.id == email_id
            ).first()
            
            return email.to_dict() if email else None
            
        except Exception as e:
            logger.error(f"❌ Error getting email: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        self.session.close()


# Singleton instance for easy access
_db_instance = None

def get_db() -> DatabaseManager:
    """
    Get database instance (singleton pattern).
    
    Usage in your code:
        from database.db_manager import get_db
        
        db = get_db()
        db.save_email(email_data)
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance