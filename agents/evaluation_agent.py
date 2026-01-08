"""
Evaluation & Optimization Agent - Self-critiques and optimizes email drafts.
Updated with proper logging.
"""

import json
import re
import logging
from typing import List, Optional
from pathlib import Path
from models.schemas import (
    EmailDraft,
    PersonaOutput,
    RetrievedTemplate,
    EvaluationMetrics,
    OptimizedEmail
)
from utils.groq_client import get_groq_client
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class EvaluationAgent:
    """
    Evaluation & Optimization Agent - Self-critique and optimization.
    OPTIMIZED: Faster evaluation with smart defaults and better accuracy.
    
    Responsibilities:
    - Evaluate email quality (5 metrics)
    - Identify issues and strengths
    - Optimize ONLY if quality < 6.5 (very low scores)
    - Generate alternative subject lines
    """
    
    # Only optimize very low scores - most emails skip optimization
    QUALITY_THRESHOLD = 6.5
    
    def __init__(self):
        """Initialize the agent."""
        self.llm = get_groq_client()
        self.evaluation_prompt = self._load_evaluation_prompt()
        self.optimization_prompt = self._load_optimization_prompt()
        
        # OPTIMIZED: Pre-compiled regex patterns for faster parsing
        self._json_pattern = re.compile(r'```(?:json)?\s*([\s\S]*?)```')
        
        # OPTIMIZED: Quick check patterns for common issues
        self._cta_time_patterns = [
            r'\d+[-\s]?minute', r'\d+[-\s]?min', r'quick call', 
            r'brief chat', r'15 min', r'10 min', r'short call'
        ]
        self._portfolio_pattern = re.compile(r'https?://[^\s]+')
    
    def _quick_quality_check(self, email: EmailDraft) -> dict:
        """OPTIMIZED: Fast pre-check to identify obvious issues/strengths."""
        checks = {
            'has_time_cta': any(re.search(p, email.cta.lower()) or re.search(p, email.body.lower()) 
                               for p in self._cta_time_patterns),
            'has_portfolio': bool(self._portfolio_pattern.search(email.body)),
            'good_length': 80 <= len(email.body.split()) <= 180,
            'short_paragraphs': all(len(p.split()) <= 50 for p in email.body.split('\n\n') if p.strip()),
        }
        return checks
    
    def _load_evaluation_prompt(self) -> PromptTemplate:
        """Load evaluation prompt."""
        prompt_path = Path("prompts/evaluation_prompt.txt")
        
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Evaluation prompt not found at {prompt_path}. "
                "Please ensure prompts/evaluation_prompt.txt exists."
            )
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return PromptTemplate.from_template(f.read())
    
    def _load_optimization_prompt(self) -> PromptTemplate:
        """Load optimization prompt."""
        prompt_path = Path("prompts/optimization_prompt.txt")
        
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Optimization prompt not found at {prompt_path}. "
                "Please ensure prompts/optimization_prompt.txt exists."
            )
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return PromptTemplate.from_template(f.read())
    
    def evaluate_and_optimize(
        self,
        email_draft: EmailDraft,
        persona: PersonaOutput,
        original_templates: List[RetrievedTemplate],
        job_role: str = "the position",
        target_company: str = "the company"
    ) -> OptimizedEmail:
        """
        Evaluate email and optimize if needed.
        Only ONE optimization pass allowed.
        """
        # Step 1: Initial evaluation with job context
        initial_evaluation = self._evaluate(email_draft, persona, job_role, target_company)
        initial_score = initial_evaluation.overall_score
        
        logger.info(f"Initial evaluation score: {initial_score:.1f}/10")
        
        # Step 2: Optimize if needed (ONLY ONE PASS)
        improvements_summary = []
        alternative_subjects_from_optimization = None
        
        if initial_score < self.QUALITY_THRESHOLD:
            logger.info(f"Score below threshold ({self.QUALITY_THRESHOLD}), optimizing...")
            optimized_draft, improvements, alt_subjects = self._optimize(email_draft, initial_evaluation, persona)
            
            # Re-evaluate optimized version with job context
            optimized_evaluation = self._evaluate(optimized_draft, persona, job_role, target_company)
            logger.info(f"Optimized version score: {optimized_evaluation.overall_score:.1f}/10")
            
            # CRITICAL: Keep whichever version scores HIGHER
            if optimized_evaluation.overall_score >= initial_score:
                # Optimization improved or maintained score - use optimized
                logger.info(f"Optimization successful: {initial_score:.1f} → {optimized_evaluation.overall_score:.1f}")
                optimization_applied = True
                improvements_summary = improvements
                alternative_subjects_from_optimization = alt_subjects
                final_evaluation = optimized_evaluation
            else:
                # Optimization made it WORSE - keep original!
                logger.warning(f"Optimization made score worse ({initial_score:.1f} → {optimized_evaluation.overall_score:.1f}), keeping original")
                optimized_draft = email_draft  # Revert to original
                optimization_applied = False
                improvements_summary = ["Optimization attempted but original scored higher"]
                alternative_subjects_from_optimization = alt_subjects  # Still keep alt subjects
                final_evaluation = initial_evaluation
        else:
            logger.info("Score above threshold, skipping optimization")
            optimized_draft = email_draft
            optimization_applied = False
            final_evaluation = initial_evaluation
        
        # Step 3: Generate alternative subject lines
        if alternative_subjects_from_optimization:
            alternative_subjects = alternative_subjects_from_optimization
        else:
            alternative_subjects = self._generate_alternative_subjects(
                optimized_draft.subject_line,
                persona,
                job_role,
                target_company
            )
        
        return OptimizedEmail(
            email=optimized_draft,
            alternative_subject_lines=alternative_subjects,
            evaluation=final_evaluation,
            optimization_applied=optimization_applied,
            initial_score=initial_score,
            improvements_summary=improvements_summary
        )
    
    def _evaluate(
        self, 
        email_draft: EmailDraft, 
        persona: PersonaOutput,
        job_role: str = "the position",
        target_company: str = "the company"
    ) -> EvaluationMetrics:
        """Evaluate email quality. OPTIMIZED: Uses quick checks for validation."""
        # OPTIMIZED: Do quick pre-checks first
        quick_checks = self._quick_quality_check(email_draft)
        
        prompt = self.evaluation_prompt.format(
            subject_line=email_draft.subject_line,
            body=email_draft.body,
            cta=email_draft.cta,
            job_role=job_role,
            target_company=target_company,
            communication_style=persona.communication_style,
            tone=persona.tone,
            pain_points=", ".join(persona.pain_points)
        )
        
        response = self.llm.invoke(prompt)
        response_text = response.content.strip()
        
        def safe_float(value, default=7.0):
            """Convert to float, clamping to valid range [0, 10]."""
            try:
                f = float(value)
                if f != f or f == float('inf') or f == float('-inf'):  # NaN or inf check
                    return default
                return max(0.0, min(10.0, f))  # Clamp to [0, 10]
            except (ValueError, TypeError):
                return default
        
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', response_text)
            eval_dict = json.loads(response_text)
            
            # OPTIMIZED: Filter out incorrect issues based on quick checks
            issues = eval_dict.get("issues", [])
            filtered_issues = []
            email_body_lower = email_draft.body.lower()
            job_role_lower = job_role.lower()
            
            for issue in issues:
                # Handle case where LLM returns dict instead of string
                if isinstance(issue, dict):
                    # Try to extract text from dict (common keys: 'text', 'issue', 'description')
                    issue = issue.get('text') or issue.get('issue') or issue.get('description') or str(issue)
                
                # Ensure issue is a string
                if not isinstance(issue, str):
                    issue = str(issue)
                    
                issue_lower = issue.lower()
                
                # Don't flag CTA as vague if it already has time commitment
                if 'cta' in issue_lower and ('vague' in issue_lower or 'time' in issue_lower):
                    if quick_checks['has_time_cta']:
                        continue  # Skip this incorrect issue
                
                # Don't flag missing portfolio if portfolio exists
                if 'portfolio' in issue_lower and 'missing' in issue_lower:
                    if quick_checks['has_portfolio']:
                        continue
                
                # Don't flag "opening doesn't mention role" if the role IS mentioned in the email
                if "doesn't mention" in issue_lower or "doesn't reference" in issue_lower or "opening" in issue_lower:
                    # Check if the job role is actually mentioned in the email body
                    role_words = [w for w in job_role_lower.split() if len(w) > 3]  # Get significant words
                    role_mentioned = any(word in email_body_lower for word in role_words)
                    if role_mentioned:
                        continue  # The role IS mentioned, skip this false issue
                
                # Filter out hardcoded/hallucinated role references
                if 'devops' in issue_lower and 'devops' not in job_role_lower:
                    continue
                if 'data scientist' in issue_lower and 'data scientist' not in job_role_lower:
                    continue
                    
                filtered_issues.append(issue)
            
            # OPTIMIZED: Add strengths based on quick checks
            strengths = eval_dict.get("strengths", [])
            
            # Normalize strengths - ensure they're strings
            normalized_strengths = []
            for strength in strengths:
                if isinstance(strength, dict):
                    strength = strength.get('text') or strength.get('strength') or strength.get('description') or str(strength)
                if not isinstance(strength, str):
                    strength = str(strength)
                normalized_strengths.append(strength)
            
            if quick_checks['has_time_cta'] and not any('cta' in s.lower() for s in normalized_strengths):
                normalized_strengths.append("CTA includes specific time commitment")
            if quick_checks['has_portfolio'] and not any('portfolio' in s.lower() for s in normalized_strengths):
                normalized_strengths.append("Portfolio link included")
            
            return EvaluationMetrics(
                clarity_score=safe_float(eval_dict.get("clarity_score", 7.0)),
                tone_alignment_score=safe_float(eval_dict.get("tone_alignment_score", 7.0)),
                length_score=safe_float(eval_dict.get("length_score", 7.0)),
                spam_risk_score=safe_float(eval_dict.get("spam_risk_score", 5.0), 5.0),
                personalization_score=safe_float(eval_dict.get("personalization_score", 7.0)),
                overall_score=safe_float(eval_dict.get("overall_score", 7.0)),
                issues=filtered_issues,
                strengths=normalized_strengths  # Use normalized strengths
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Evaluation parsing failed, using defaults. Error: {e}")
            return EvaluationMetrics(
                clarity_score=7.0,
                tone_alignment_score=7.0,
                length_score=7.0,
                spam_risk_score=5.0,
                personalization_score=7.0,
                overall_score=7.0,
                issues=[],
                strengths=["Generated successfully"]
            )
    
    def _optimize(
        self,
        email_draft: EmailDraft,
        evaluation: EvaluationMetrics,
        persona: PersonaOutput
    ) -> tuple[EmailDraft, List[str], Optional[List[str]]]:
        """Optimize email based on evaluation."""
        prompt = self.optimization_prompt.format(
            subject_line=email_draft.subject_line,
            body=email_draft.body,
            cta=email_draft.cta,
            issues="\n".join(evaluation.issues),
            communication_style=persona.communication_style,
            tone=persona.tone,
            value_focus=persona.value_focus
        )
        
        response = self.llm.invoke(prompt)
        response_text = response.content.strip()
        
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', response_text)
            opt_dict = json.loads(response_text)
            
            optimized_draft = EmailDraft(
                subject_line=opt_dict.get("subject_line", email_draft.subject_line),
                body=opt_dict.get("body", email_draft.body),
                cta=opt_dict.get("cta", email_draft.cta)
            )
            
            improvements = opt_dict.get("improvements_applied", [])
            if not improvements and evaluation.issues:
                improvements = [f"Addressed: {issue}" for issue in evaluation.issues[:3]]
            elif not improvements:
                improvements = ["Refined email based on evaluation"]
            
            # Normalize improvements - ensure they're strings
            normalized_improvements = []
            for improvement in improvements:
                if isinstance(improvement, dict):
                    improvement = improvement.get('text') or improvement.get('improvement') or str(improvement)
                if not isinstance(improvement, str):
                    improvement = str(improvement)
                normalized_improvements.append(improvement)
            
            alternative_subjects = opt_dict.get("alternative_subject_lines", None)
            
            # Normalize alternative subjects - ensure they're strings
            if alternative_subjects:
                normalized_alt_subjects = []
                for subject in alternative_subjects:
                    if isinstance(subject, dict):
                        subject = subject.get('text') or subject.get('subject') or str(subject)
                    if not isinstance(subject, str):
                        subject = str(subject)
                    normalized_alt_subjects.append(subject)
                alternative_subjects = normalized_alt_subjects
            
            return optimized_draft, normalized_improvements, alternative_subjects
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Optimization parsing failed, using original. Error: {e}")
            return email_draft, ["Optimization attempted but parsing failed"], None
    
    def _generate_alternative_subjects(
        self,
        original_subject: str,
        persona: PersonaOutput,
        job_role: str = "the position",
        company_name: str = "the company"
    ) -> List[str]:
        """Generate 2-3 alternative subject lines with actual company and role names."""
        prompt = f"""Generate 3 alternative subject lines for a B2B cold email.

Original subject: {original_subject}
Tone: {persona.tone}
Company Name: {company_name}
Job Role: {job_role}

RULES (CRITICAL):
- Each subject must be 40-55 characters MAX
- Professional and business-appropriate
- MUST use the actual company name "{company_name}" - NOT [Company] placeholder
- MUST use the actual role "{job_role}" - NOT [Role] placeholder
- Sound respectful and relevant
- NO placeholders like [Company] or [Role] - use actual names!
- NO corporate jargon (avoid: leverage, unlock, accelerate, optimize, solutions)
- NO spam words (avoid: FREE, URGENT, exclusive, guaranteed)

GOOD examples using actual names:
- "Regarding {company_name}'s {job_role} opening"
- "{job_role} hiring - an alternative approach"
- "Supporting {company_name}'s {job_role} needs"
- "{company_name} + partnership opportunity"

BAD examples (don't do this):
- "Regarding [Company]'s [Role] opening" ❌ uses placeholders
- "Exploring Opportunities for Accelerated Development" ❌ too long, corporate
- "Quick question about..." ❌ too casual

Return ONLY a JSON array with 3 professional subjects using ACTUAL company/role names:
["subject 1", "subject 2", "subject 3"]"""
        
        response = self.llm.invoke(prompt)
        response_text = response.content.strip()
        
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', response_text)
            subjects = json.loads(response_text)
            
            if isinstance(subjects, list):
                # Normalize subjects - ensure they're strings
                normalized_subjects = []
                for subject in subjects[:3]:
                    if isinstance(subject, dict):
                        subject = subject.get('text') or subject.get('subject') or str(subject)
                    if not isinstance(subject, str):
                        subject = str(subject)
                    normalized_subjects.append(subject)
                return normalized_subjects
            return [original_subject]
        except (json.JSONDecodeError, TypeError):
            return [original_subject, f"Re: {original_subject}", f"Quick question: {original_subject[:30]}"]