"""
Cold Outreach AI Agent - Database Package
Contains database models and management utilities.
"""

from database.db_manager import DatabaseManager, get_db
from database.models import EmailGeneration, TemplateUsage

__all__ = ['DatabaseManager', 'get_db', 'EmailGeneration', 'TemplateUsage']