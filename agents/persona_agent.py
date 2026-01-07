"""
Persona Analyzer Agent - Analyzes target recipient persona.
OPTIMIZED: Smart caching, extensive role mappings, faster defaults.
"""

import json
import logging
from pathlib import Path
from models.schemas import PersonaInput, PersonaOutput
from utils.groq_client import get_groq_client
from langchain.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class PersonaAnalyzerAgent:
    """
    Persona Analyzer Agent - Extracts insights about target persona.
    OPTIMIZED: Extensive caching, smart defaults, role-based intelligence.
    
    Responsibilities:
    - Analyze role, industry, and product context
    - Infer pain points and decision drivers
    - Determine communication style
    - Recommend tone and value focus
    """
    
    # Cache for repeated role/industry combinations
    _persona_cache: dict = {}
    
    def __init__(self):
        """Initialize the agent with prompt template."""
        self.llm = get_groq_client()
        self.prompt_template = self._load_prompt()
        
        # OPTIMIZED: Extensive pre-defined pain points for ALL common roles
        self.common_pain_points = {
            # Engineering roles
            "software engineer": ["lengthy hiring process (3-6 months)", "finding quality candidates", "technical skill validation", "team scaling challenges"],
            "senior software engineer": ["architecture decisions", "mentoring junior developers", "technical debt management", "cross-team coordination"],
            "staff engineer": ["system design complexity", "organizational alignment", "technical strategy", "stakeholder management"],
            "principal engineer": ["long-term technical vision", "company-wide standards", "build vs buy decisions", "technical leadership"],
            
            # Data & ML roles
            "data scientist": ["ML infrastructure complexity", "model deployment challenges", "data pipeline management", "experiment tracking"],
            "data analyst": ["data quality issues", "reporting automation", "stakeholder communication", "tool fragmentation"],
            "machine learning engineer": ["model training at scale", "MLOps complexity", "production deployment", "model monitoring"],
            "ml engineer": ["model training at scale", "MLOps complexity", "production deployment", "feature engineering"],
            "data engineer": ["pipeline reliability", "data quality", "schema evolution", "processing at scale"],
            
            # Frontend/Backend roles
            "frontend engineer": ["UI/UX consistency", "cross-browser compatibility", "performance optimization", "state management"],
            "backend engineer": ["API design", "database optimization", "system scalability", "security concerns"],
            "full stack": ["end-to-end delivery", "technology stack decisions", "rapid prototyping", "context switching"],
            "fullstack": ["end-to-end delivery", "technology stack decisions", "rapid prototyping", "context switching"],
            
            # DevOps/Infrastructure roles
            "devops engineer": ["CI/CD automation", "infrastructure scaling", "security compliance", "incident response"],
            "cloud engineer": ["cloud cost optimization", "multi-cloud complexity", "security configuration", "migration challenges"],
            "sre": ["reliability targets", "incident management", "capacity planning", "automation backlog"],
            "site reliability": ["reliability targets", "incident management", "capacity planning", "automation backlog"],
            "platform engineer": ["developer experience", "self-service infrastructure", "standardization", "tooling adoption"],
            
            # Leadership roles
            "engineering manager": ["team productivity", "hiring quality engineers", "retention challenges", "delivery timelines"],
            "tech lead": ["technical decisions", "code quality", "team mentoring", "stakeholder alignment"],
            "cto": ["technology strategy", "team scaling", "build vs buy", "technical debt"],
            "vp engineering": ["organizational scaling", "engineering culture", "delivery predictability", "talent acquisition"],
        }
        
        # OPTIMIZED: Pre-defined value focus by role type
        self.value_focus_map = {
            "engineer": "technical excellence and delivery speed",
            "scientist": "research quality and production impact",
            "analyst": "data-driven insights and reporting efficiency",
            "manager": "team productivity and delivery outcomes",
            "lead": "technical leadership and team growth",
            "devops": "reliability and automation",
            "cloud": "infrastructure efficiency and cost optimization",
        }
    
    def _load_prompt(self) -> PromptTemplate:
        """Load persona analysis prompt from file."""
        prompt_path = Path("prompts/persona_prompt.txt")
        
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Persona prompt not found at {prompt_path}. "
                "Please ensure prompts/persona_prompt.txt exists."
            )
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return PromptTemplate.from_template(f.read())
    
    def analyze(self, input_data: PersonaInput) -> PersonaOutput:
        """
        Analyze persona and return structured insights.
        OPTIMIZED: Uses cache and smart defaults for speed.
        
        Args:
            input_data: PersonaInput with role, industry, product, tone
            
        Returns:
            PersonaOutput with structured persona insights
        """
        # OPTIMIZED: Check cache first for repeated requests
        cache_key = f"{input_data.role.lower()}_{input_data.industry.lower()}_{input_data.tone}"
        if cache_key in PersonaAnalyzerAgent._persona_cache:
            logger.info(f"⚡ Using cached persona for {input_data.role}")
            return PersonaAnalyzerAgent._persona_cache[cache_key]
        
        # OPTIMIZED: Get pre-defined pain points if available
        role_lower = input_data.role.lower()
        default_pain_points = None
        for key, points in self.common_pain_points.items():
            if key in role_lower:
                default_pain_points = points
                break
        
        try:
            # Format prompt with optional job data
            job_data_section = ""
            if input_data.scraped_job_data:
                job_data = input_data.scraped_job_data
                job_data_section = f"""
IMPORTANT: High-confidence evidence from job posting:
- Role (from posting): {job_data.role}
- Company: {job_data.company if job_data.company else 'Not specified'}
- Required Skills: {', '.join(job_data.skills) if job_data.skills else 'Not specified'}
- Experience Level: {job_data.experience if job_data.experience else 'Not specified'}
- Key Responsibilities: {', '.join(job_data.responsibilities) if job_data.responsibilities else 'Not specified'}
- Keywords: {', '.join(job_data.keywords) if job_data.keywords else 'Not specified'}

Use this EXACT information from the job posting as high-confidence evidence. 
The pain points and needs should be directly inferred from these responsibilities and requirements.
"""
            
            prompt = self.prompt_template.format(
                role=input_data.role,
                industry=input_data.industry,
                tone=input_data.tone,
                job_data_section=job_data_section
            )
            
            # Get LLM response
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON response
            try:
                # Extract JSON from response
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                persona_dict = json.loads(response_text)
                
                # Validate and create PersonaOutput
                result = PersonaOutput(
                    pain_points=persona_dict.get("pain_points", default_pain_points or []),
                    decision_drivers=persona_dict.get("decision_drivers", []),
                    communication_style=persona_dict.get("communication_style", "Professional"),
                    tone=persona_dict.get("tone", input_data.tone),
                    value_focus=persona_dict.get("value_focus", "Value proposition")
                )
                
                # OPTIMIZED: Cache the result for future requests
                PersonaAnalyzerAgent._persona_cache[cache_key] = result
                return result
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails - use pre-defined pain points if available
                logger.warning(f"JSON parsing failed, using fallback. Error: {e}")
                return PersonaOutput(
                    pain_points=default_pain_points or ["Efficiency challenges", "Resource constraints"],
                    decision_drivers=["ROI", "Time savings", "Quality"],
                    communication_style="Professional and concise",
                    tone=input_data.tone,
                    value_focus="Operational efficiency"
                )
        except Exception as e:
            logger.error(f"Unexpected error in persona analysis: {e}", exc_info=True)
            # Return fallback persona with pre-defined pain points
            return PersonaOutput(
                pain_points=default_pain_points or ["Efficiency challenges", "Resource constraints"],
                decision_drivers=["ROI", "Time savings", "Quality"],
                communication_style="Professional and concise",
                tone=input_data.tone,
                value_focus="Operational efficiency"
            )