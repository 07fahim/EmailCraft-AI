"""
Export Utilities - Save data to CSV/Excel.

Simple functions for exporting:
- export_to_csv() - Save to CSV file
- export_to_excel() - Save to Excel file
- prepare_export_data() - Format data for export
"""

import pandas as pd
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def prepare_export_data(emails: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert email data to pandas DataFrame for export.
    
    Args:
        emails: List of email dictionaries from database
        
    Returns:
        pandas DataFrame ready for export
    """
    if not emails:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(emails)
    
    # Select and order columns for export
    export_columns = [
        'id', 'timestamp', 'company_name', 'recipient_name',
        'role', 'industry', 'subject_line', 'body', 'cta',
        'final_score', 'initial_score', 'optimization_applied',
        'templates_used', 'portfolio_items_used'
    ]
    
    # Keep only columns that exist
    available_columns = [col for col in export_columns if col in df.columns]
    df = df[available_columns]
    
    # Format timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Rename columns for better readability
    column_names = {
        'id': 'Email ID',
        'timestamp': 'Generated At',
        'company_name': 'Company',
        'recipient_name': 'Recipient',
        'role': 'Target Role',
        'industry': 'Industry',
        'subject_line': 'Subject Line',
        'body': 'Email Body',
        'cta': 'Call to Action',
        'final_score': 'Quality Score',
        'initial_score': 'Initial Score',
        'optimization_applied': 'Optimized',
        'templates_used': 'Templates Used',
        'portfolio_items_used': 'Portfolio Items'
    }
    
    df = df.rename(columns=column_names)
    
    return df


def export_to_csv(emails: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Export emails to CSV file.
    
    Args:
        emails: List of email dictionaries
        filename: Output filename (auto-generated if None)
        
    Returns:
        Path to saved file
    
    Example:
        from database.db_manager import get_db
        from utils.export_utils import export_to_csv
        
        db = get_db()
        emails = db.get_all_emails()
        filepath = export_to_csv(emails)
        print(f"Saved to: {filepath}")
    """
    try:
        # Prepare data
        df = prepare_export_data(emails)
        
        if df.empty:
            logger.warning("No data to export")
            return None
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cold_emails_export_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        
        logger.info(f"✅ Exported {len(df)} emails to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error exporting to CSV: {e}")
        return None


def export_to_excel(emails: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Export emails to Excel file with formatting.
    
    Args:
        emails: List of email dictionaries
        filename: Output filename (auto-generated if None)
        
    Returns:
        Path to saved file
    """
    try:
        # Prepare data
        df = prepare_export_data(emails)
        
        if df.empty:
            logger.warning("No data to export")
            return None
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cold_emails_export_{timestamp}.xlsx"
        
        # Save to Excel with formatting
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Generated Emails', index=False)
            
            # Get worksheet
            worksheet = writer.sheets['Generated Emails']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Max 50 chars
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"✅ Exported {len(df)} emails to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error exporting to Excel: {e}")
        return None


def export_analytics_summary(analytics: Dict[str, Any], filename: str = None) -> str:
    """
    Export analytics summary to CSV.
    
    Args:
        analytics: Analytics dictionary from db.get_analytics()
        filename: Output filename
        
    Returns:
        Path to saved file
    """
    try:
        # Convert analytics to DataFrame
        summary_data = {
            'Metric': [
                'Total Emails Generated',
                'Average Quality Score',
                'Success Rate (>= 8.5)',
                'Optimization Rate',
                'Recent Activity (7 days)'
            ],
            'Value': [
                analytics['total_emails'],
                f"{analytics['average_score']}/10",
                f"{analytics['success_rate']}%",
                f"{analytics['optimization_rate']}%",
                analytics['recent_activity_7days']
            ]
        }
        
        df = pd.DataFrame(summary_data)
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analytics_summary_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        
        logger.info(f"✅ Exported analytics summary to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error exporting analytics: {e}")
        return None