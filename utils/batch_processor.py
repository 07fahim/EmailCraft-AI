"""
Batch CSV Processing - Generate multiple emails from CSV file.
Enables high-volume email generation for agencies and teams.
"""

import os
import pandas as pd
import logging
import math
import json
import re
import time
from typing import Dict, Any, Tuple
from io import StringIO
import requests

logger = logging.getLogger(__name__)

# Detect if running in production (Render sets this)
IS_PRODUCTION = bool(os.getenv("RENDER") or os.getenv("PINECONE_API_KEY"))
# Delay between emails: 30s in production (rate limits), 2s locally
BATCH_DELAY = 30 if IS_PRODUCTION else 2


def safe_float(val, default=0.0) -> float:
    """Safely convert to float, handling inf/nan/None."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def sanitize_json_text(text: str) -> str:
    """Remove inf/nan values from JSON text before parsing."""
    # Replace various inf/nan formats with 0
    text = re.sub(r':\s*Infinity\b', ': 0', text)
    text = re.sub(r':\s*-Infinity\b', ': 0', text)
    text = re.sub(r':\s*NaN\b', ': 0', text)
    text = re.sub(r':\s*inf\b', ': 0', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*-inf\b', ': 0', text, flags=re.IGNORECASE)
    text = re.sub(r':\s*nan\b', ': 0', text, flags=re.IGNORECASE)
    return text


def parse_response_safely(response) -> dict:
    """Parse API response, handling inf/nan values."""
    try:
        # First, sanitize the raw text
        raw_text = response.text
        clean_text = sanitize_json_text(raw_text)
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        logger.error(f"Response text (first 500 chars): {response.text[:500]}")
        raise


class BatchEmailProcessor:
    """
    Handles batch email generation from CSV files.
    
    CSV Format:
    job_url, company_name, recipient_name, sender_name, sender_company, sender_services
    """
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
    
    def validate_csv(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate CSV format and required columns."""
        required_columns = ['job_url', 'company_name']
        
        # Check for required columns
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"
        
        # Check for empty required fields
        for col in required_columns:
            if df[col].isna().any():
                empty_rows = df[df[col].isna()].index.tolist()
                return False, f"Column '{col}' has empty values in rows: {empty_rows}"
        
        # Check row count
        if len(df) < 1:
            return False, "CSV file must contain at least 1 row of data"
        if len(df) > 200:
            return False, "CSV file cannot exceed 200 rows. Please split into smaller batches."
        
        return True, ""
    
    def process_batch(
        self, 
        csv_content: str, 
        progress_callback=None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process batch of emails from CSV content."""
        # Parse CSV
        df = pd.read_csv(StringIO(csv_content))
        
        # Validate
        is_valid, error = self.validate_csv(df)
        if not is_valid:
            raise ValueError(error)
        
        # Initialize results
        results = []
        stats = {
            'total': len(df),
            'successful': 0,
            'failed': 0,
            'average_score': 0.0,
            'errors': []
        }
        total_score = 0.0
        
        # Process each row
        for idx, row in df.iterrows():
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(df), f"Processing {row['company_name']}...")
                
                # Build request payload
                payload = {
                    'job_url': str(row['job_url']),
                    'company_name': str(row['company_name']),
                    'recipient_name': str(row.get('recipient_name', '')) if pd.notna(row.get('recipient_name')) else None,
                    'sender_name': str(row.get('sender_name', 'Alex')) if pd.notna(row.get('sender_name')) else 'Alex',
                    'sender_company': str(row.get('sender_company', 'TechSolutions Inc.')) if pd.notna(row.get('sender_company')) else 'TechSolutions Inc.',
                    'sender_services': str(row.get('sender_services', 'software development')) if pd.notna(row.get('sender_services')) else 'software development',
                    'tone': 'professional'
                }
                
                # Call API with retry logic
                max_retries = 3
                response = None
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        response = requests.post(
                            f"{self.api_url}/generate-email",
                            json=payload,
                            timeout=180  # Increased timeout for production
                        )
                        if response.status_code in [502, 503, 504, 429]:
                            # Retry on server errors or rate limits
                            wait_time = 3 * (attempt + 1)  # 3, 6, 9 seconds
                            logger.warning(f"Row {idx + 1}: HTTP {response.status_code}, retrying in {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        break  # Success or non-retryable error
                    except requests.exceptions.Timeout:
                        last_error = "Request timeout"
                        wait_time = 5 * (attempt + 1)
                        logger.warning(f"Row {idx + 1}: Timeout, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    except requests.exceptions.RequestException as e:
                        last_error = str(e)
                        break  # Don't retry on connection errors
                
                # Handle case where all retries failed
                if response is None:
                    results.append({
                        'row_number': idx + 1,
                        'company_name': str(row.get('company_name', 'Unknown')),
                        'recipient_name': str(row.get('recipient_name', '')),
                        'job_url': str(row.get('job_url', '')),
                        'subject_line': '',
                        'email_body': '',
                        'cta': '',
                        'quality_score': 0,
                        'status': f'Failed: {last_error or "Connection error"}'
                    })
                    stats['failed'] += 1
                    stats['errors'].append(f"Row {idx + 1}: {last_error or 'Connection error'}")
                    # Add delay before next request to avoid overload
                    time.sleep(2)
                    continue
                
                if response.status_code == 200:
                    # Parse response safely
                    response_data = parse_response_safely(response)
                    data = response_data.get('data', {})
                    
                    # Extract with safe defaults
                    final_email = data.get('final_email', {})
                    eval_details = data.get('evaluation_details', {})
                    alt_subjects = data.get('alternative_subject_lines', [])
                    
                    # Build result with all values sanitized
                    score = safe_float(data.get('final_score', 0), 0)
                    
                    result = {
                        'row_number': idx + 1,
                        'company_name': row['company_name'],
                        'recipient_name': str(row.get('recipient_name', 'NOT_PROVIDED')) if pd.notna(row.get('recipient_name')) else 'NOT_PROVIDED',
                        'job_url': row['job_url'],
                        'subject_line': final_email.get('subject_line', ''),
                        'email_body': final_email.get('body', ''),
                        'cta': final_email.get('cta', ''),
                        'quality_score': score,
                        'clarity_score': safe_float(eval_details.get('clarity_score', 0)),
                        'tone_score': safe_float(eval_details.get('tone_alignment_score', 0)),
                        'length_score': safe_float(eval_details.get('length_score', 0)),
                        'personalization_score': safe_float(eval_details.get('personalization_score', 0)),
                        'spam_risk_score': safe_float(eval_details.get('spam_risk_score', 0)),
                        'optimization_applied': data.get('optimization_applied', False),
                        'alternative_subject_1': alt_subjects[0] if len(alt_subjects) > 0 else '',
                        'alternative_subject_2': alt_subjects[1] if len(alt_subjects) > 1 else '',
                        'alternative_subject_3': alt_subjects[2] if len(alt_subjects) > 2 else '',
                        'status': 'Success'
                    }
                    
                    results.append(result)
                    stats['successful'] += 1
                    total_score += score
                    
                    # Delay between emails: 30s in production (rate limits), 2s locally
                    if idx < len(df) - 1:  # Don't delay after last email
                        logger.info(f"⏳ Waiting {BATCH_DELAY}s before next email...")
                        time.sleep(BATCH_DELAY)
                    
                else:
                    # API error - also parse safely
                    try:
                        err_data = parse_response_safely(response)
                        error_msg = err_data.get('detail', 'Unknown error')
                    except:
                        error_msg = f"HTTP {response.status_code}"
                    
                    results.append({
                        'row_number': idx + 1,
                        'company_name': row['company_name'],
                        'recipient_name': str(row.get('recipient_name', '')),
                        'job_url': row['job_url'],
                        'subject_line': '',
                        'email_body': '',
                        'cta': '',
                        'quality_score': 0,
                        'status': f'Failed: {error_msg}'
                    })
                    stats['failed'] += 1
                    stats['errors'].append(f"Row {idx + 1}: {error_msg}")
                    
                    # Delay after failure: 30s in production, 2s locally
                    logger.info(f"⏳ Waiting {BATCH_DELAY}s after failure...")
                    time.sleep(BATCH_DELAY)
                    
            except Exception as e:
                logger.error(f"Error processing row {idx + 1}: {e}")
                results.append({
                    'row_number': idx + 1,
                    'company_name': str(row.get('company_name', 'Unknown')),
                    'recipient_name': str(row.get('recipient_name', '')),
                    'job_url': str(row.get('job_url', '')),
                    'subject_line': '',
                    'email_body': '',
                    'cta': '',
                    'quality_score': 0,
                    'status': f'Error: {str(e)[:100]}'
                })
                stats['failed'] += 1
                stats['errors'].append(f"Row {idx + 1}: {str(e)}")
                
                # Delay after error: 30s in production, 2s locally
                logger.info(f"⏳ Waiting {BATCH_DELAY}s after error...")
                time.sleep(BATCH_DELAY)
        
        # Calculate average score safely
        if stats['successful'] > 0:
            stats['average_score'] = safe_float(total_score / stats['successful'], 0)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        return results_df, stats


def create_sample_csv() -> str:
    """Create a sample CSV template for batch processing."""
    sample_data = """job_url,company_name,recipient_name,sender_name,sender_company,sender_services
https://www.linkedin.com/jobs/view/123456,Acme Corp,Sarah Chen,Alex,TechSolutions Inc.,software development and consulting services
https://careers.google.com/jobs/results/789012,Google,Mike Johnson,Alex,TechSolutions Inc.,AI and machine learning solutions
https://jobs.apple.com/en-us/details/345678,Apple,Lisa Wang,Alex,TechSolutions Inc.,mobile app development and cloud infrastructure"""
    
    return sample_data
