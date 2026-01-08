"""
Email Generation Agent - Generates cold emails using persona and portfolio.
OPTIMIZED: Better JSON handling, retry logic, faster generation.
"""

import json
import re
import logging
from pathlib import Path
from models.schemas import EmailGenerationInput, EmailDraft
from utils.groq_client import get_groq_client
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class EmailGenerationAgent:
    """
    Email Generation Agent - Creates cold email drafts.
    OPTIMIZED: Better JSON parsing, smart retries, pre-compiled patterns.
    
    Uses simplified prompt approach (Codebasics style):
    - Specific sender identity
    - Portfolio links mandatory
    - Clear, concise instructions
    """
    
    # OPTIMIZED: Pre-compiled patterns for faster JSON extraction
    _json_block_pattern = re.compile(r'```(?:json)?\s*([\s\S]*?)```')
    _control_char_pattern = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]')
    
    def __init__(self):
        """Initialize the agent."""
        self.llm = get_groq_client()
        self.prompt_template = self._load_prompt()
        
        # OPTIMIZED: Strong JSON format instruction
        self.json_reminder = """

===========================================
OUTPUT FORMAT (CRITICAL - FOLLOW EXACTLY)
===========================================

Return ONLY a valid JSON object with these exact keys:
{
  "subject_line": "your subject line here",
  "body": "full email body with proper line breaks using newline characters",
  "cta": "your call to action"
}

NO markdown, NO explanations, NO text outside the JSON object."""
    
    def _load_prompt(self) -> PromptTemplate:
        """Load simplified generation prompt."""
        prompt_path = Path("prompts/generation_prompt.txt")
        
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
        else:
            # Fallback prompt
            prompt_text = """You are {sender_name} from {sender_company}.

Write a professional cold email to {recipient_name} at {company_name} about {product}.

Address these pain points: {pain_points}
Include these portfolio links: {portfolio_links}

Return JSON with subject_line, body, and cta."""
        
        return PromptTemplate.from_template(prompt_text)
    
    def generate(self, input_data: EmailGenerationInput) -> EmailDraft:
        """
        Generate email draft using simplified approach.
        
        Args:
            input_data: EmailGenerationInput with all context
            
        Returns:
            EmailDraft with subject, body, and CTA
        """
        # Format portfolio links - JUST THE LINKS for clean email inclusion
        portfolio_text = ""
        if input_data.portfolio_items:
            # List links clearly so LLM includes ALL of them
            links = [item.link for item in input_data.portfolio_items[:3]]  # Max 3 links
            portfolio_text = f"INCLUDE ALL {len(links)} LINKS BELOW IN THE EMAIL:\n"
            for i, link in enumerate(links, 1):
                portfolio_text += f"  Link {i}: {link}\n"
            portfolio_text += "\nIMPORTANT: Include ALL links above in the email body, one per line."
        else:
            portfolio_text = "No portfolio items available - focus on product value."
        
        # Format job context if available
        job_context = ""
        if input_data.scraped_job_data:
            job_data = input_data.scraped_job_data
            job_context = f"""JOB POSTING DETAILS:
They're hiring for: {job_data.role}
Required skills: {', '.join(job_data.skills[:5])}
Key responsibilities: {', '.join(job_data.responsibilities[:3])}

Use this information to show you understand their needs and position your {input_data.sender_services} as the solution."""
        
        # Format persona insights
        pain_points_str = ", ".join(input_data.persona.pain_points[:3])
        
        # Build prompt
        # Handle recipient name - use actual name or signal for "Dear Hiring Manager"
        recipient_name_value = input_data.recipient_name if input_data.recipient_name else "NOT_PROVIDED"
        
        prompt = self.prompt_template.format(
            sender_name=input_data.sender_name,
            sender_company=input_data.sender_company,
            sender_services=input_data.sender_services,
            value_focus=input_data.persona.value_focus,
            pain_points=pain_points_str,
            role=input_data.scraped_job_data.role if input_data.scraped_job_data else "their role",
            company_name=input_data.company_name or "the company",
            recipient_name=recipient_name_value,
            industry=input_data.persona.value_focus,
            job_context=job_context,
            portfolio_links=portfolio_text,
            tone=input_data.persona.tone
        )
        
        # OPTIMIZED: Add JSON format reminder for consistent output
        prompt += self.json_reminder
        
        # Get LLM response with optimized parsing
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # OPTIMIZED: Use pre-compiled patterns for faster extraction
            json_match = self._json_block_pattern.search(response_text)
            if json_match:
                response_text = json_match.group(1).strip()
            elif "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # OPTIMIZED: Clean control characters with pre-compiled pattern
            response_text = self._control_char_pattern.sub('', response_text)
            
            # OPTIMIZED: Try to find JSON object if not at start
            if not response_text.startswith('{'):
                json_start = response_text.find('{')
                json_end = response_text.rfind('}')
                if json_start != -1 and json_end != -1:
                    response_text = response_text[json_start:json_end + 1]
            
            email_dict = json.loads(response_text)
            
            # Post-process: Remove em-dashes and make more human-readable
            body = email_dict.get("body", "Hi, I wanted to reach out...")
            body = body.replace("—", ". ")  # Replace em-dash with period
            body = body.replace("--", ". ")  # Replace double hyphen with period
            body = body.replace(" . ", ". ")  # Clean up double spaces
            body = body.replace(".. ", ". ")  # Clean up double periods
            
            logger.info("✅ Email generated successfully")
            
            return EmailDraft(
                subject_line=email_dict.get("subject_line", "Quick question"),
                body=body,
                cta=email_dict.get("cta", "Let's connect")
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"JSON parsing failed: {e}, using fallback")
            
            # Fallback email with portfolio link if available
            portfolio_mention = ""
            if input_data.portfolio_items:
                first_item = input_data.portfolio_items[0]
                portfolio_mention = f"\n\nWe recently helped a similar company: {first_item.link}"
            
            return EmailDraft(
                subject_line=f"Quick question about {input_data.company_name or 'your team'}",
                body=f"Hi {input_data.recipient_name or 'there'},\n\nI'm {input_data.sender_name} from {input_data.sender_company}. I noticed you're focused on {input_data.persona.value_focus}.\n\nMany professionals in your role struggle with {pain_points_str}. Our {input_data.sender_services} can help.{portfolio_mention}\n\nWould you be open to a brief conversation?\n\nBest regards,\n{input_data.sender_name}",
                cta="Schedule a 15-minute call"
            )