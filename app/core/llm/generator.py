"""
LLM-based Report Generator
Generates formal safety incident reports using Large Language Models.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

from loguru import logger
import openai
import google.generativeai as genai

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class ReportFormat(Enum):
    """Report output formats."""
    FORMAL = "formal"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    EMAIL = "email"


@dataclass
class ReportMetadata:
    """Metadata for incident report."""
    location: str
    timestamp: datetime
    inspector_id: Optional[str] = None
    site_id: Optional[str] = None
    shift: Optional[str] = None
    weather_conditions: Optional[str] = None
    camera_id: Optional[str] = None


@dataclass
class IncidentReport:
    """Complete incident report object."""
    report_id: str
    title: str
    text: str
    metadata: ReportMetadata
    violations: List[Dict]
    recommendations: List[str]
    format: ReportFormat
    generated_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "title": self.title,
            "text": self.text,
            "metadata": {
                "location": self.metadata.location,
                "timestamp": self.metadata.timestamp.isoformat(),
                "inspector_id": self.metadata.inspector_id,
                "site_id": self.metadata.site_id,
                "shift": self.metadata.shift,
                "weather_conditions": self.metadata.weather_conditions,
                "camera_id": self.metadata.camera_id
            },
            "violations": self.violations,
            "recommendations": self.recommendations,
            "format": self.format.value,
            "generated_at": self.generated_at.isoformat()
        }


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 1500
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert workplace safety officer with deep knowledge of OSHA regulations and industrial safety standards."},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-pro",
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
        
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini API."""
        try:
            generation_config = {
                "temperature": kwargs.get("temperature", self.temperature),
                "max_output_tokens": kwargs.get("max_tokens", 1500)
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3
    ):
        if not REQUESTS_AVAILABLE:
            raise ValueError("requests library required for Ollama. Install with: pip install requests")
        
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        
        # Test connection
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                logger.info(f"Connected to Ollama. Available models: {model_names}")
                
                # Check if requested model is available
                if model not in model_names and f"{model}:latest" not in model_names:
                    logger.warning(f"Model '{model}' not found. Run: ollama pull {model}")
            else:
                logger.warning(f"Ollama server responded with status {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: https://ollama.ai")
        
        logger.info(f"Initialized Ollama provider with model: {model}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama API."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", self.temperature),
                        "num_predict": kwargs.get("max_tokens", 1500)
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                error_msg = f"Ollama request failed with status {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise


class ReportGenerator:
    """
    Production-ready safety report generator using LLMs.
    
    Features:
    - Multiple LLM provider support (OpenAI, Gemini)
    - Customizable report templates
    - OSHA/ISO standards citation
    - Structured report formatting
    - Recommendation engine
    """
    
    REPORT_TEMPLATES = {
        ReportFormat.FORMAL: """
You are a certified workplace safety officer preparing a formal incident report for management review.

Based on the following workplace safety violation details, generate a comprehensive, professional incident report:

VIOLATION DETAILS:
{violation_details}

LOCATION: {location}
DATE/TIME: {timestamp}
SITE ID: {site_id}
INSPECTOR: {inspector_id}

Generate a formal incident report with the following structure:

1. INCIDENT SUMMARY
   - Brief description of the violation(s) detected
   
2. DETAILED FINDINGS
   - Specific PPE violations identified
   - Severity classification
   - Applicable OSHA/ISO standards violated
   
3. RISK ASSESSMENT
   - Potential hazards and consequences
   - Likelihood and severity rating
   
4. CORRECTIVE ACTIONS REQUIRED
   - Immediate actions needed
   - Long-term preventive measures
   - Training recommendations
   
5. COMPLIANCE CITATIONS
   - Specific OSHA regulations (29 CFR)
   - ISO safety standards if applicable
   
6. FOLLOW-UP REQUIREMENTS
   - Timeline for corrective actions
   - Verification procedures

The report should be professional, factual, and actionable. Use formal business language appropriate for management review and potential regulatory submission.
""",
        
        ReportFormat.TECHNICAL: """
Generate a technical safety analysis report based on the following violation data:

{violation_details}

Focus on:
- Technical specifications of PPE requirements
- Quantitative risk metrics
- Engineering controls needed
- Detailed compliance matrix with specific regulation sections
- Statistical analysis if multiple violations

Location: {location}
Timestamp: {timestamp}
""",
        
        ReportFormat.EXECUTIVE: """
Create an executive summary of the following workplace safety incident:

{violation_details}

The summary should be:
- Concise (max 2 paragraphs)
- Focus on business impact and liability exposure
- Include clear action items for leadership
- Highlight urgent vs. routine corrective actions

Location: {location}
Date: {timestamp}
""",
        
        ReportFormat.EMAIL: """
Draft a professional email to site management regarding the following safety violation:

{violation_details}

Location: {location}
Date/Time: {timestamp}

The email should:
- Have a clear subject line
- Be professional but urgent in tone
- Clearly state required immediate actions
- Include a deadline for response
- Cite relevant safety regulations
"""
    }
    
    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        temperature: float = 0.3,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize report generator.
        
        Args:
            provider: LLM provider ('openai', 'gemini', or 'ollama')
            model: Specific model to use (provider-dependent)
            temperature: Generation temperature (0.0-1.0)
            api_key: API key (optional, for cloud providers)
            base_url: Base URL (optional, for Ollama)
        """
        self.provider_name = provider.lower()
        
        # Initialize appropriate provider
        if self.provider_name == "openai":
            model = model or "gpt-4o"
            self.provider = OpenAIProvider(
                api_key=api_key,
                model=model,
                temperature=temperature
            )
        elif self.provider_name == "gemini":
            model = model or "gemini-pro"
            self.provider = GeminiProvider(
                api_key=api_key,
                model=model,
                temperature=temperature
            )
        elif self.provider_name == "ollama":
            model = model or "llama3"
            self.provider = OllamaProvider(
                model=model,
                base_url=base_url or "http://localhost:11434",
                temperature=temperature
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai', 'gemini', or 'ollama'")
        
        logger.success(f"Report generator initialized with {provider} provider")
    
    def generate_report(
        self,
        violations: List[Dict],
        metadata: ReportMetadata,
        format: ReportFormat = ReportFormat.FORMAL,
        custom_template: Optional[str] = None
    ) -> IncidentReport:
        """
        Generate incident report from violations.
        
        Args:
            violations: List of violation dictionaries
            metadata: Report metadata
            format: Report format type
            custom_template: Optional custom prompt template
            
        Returns:
            IncidentReport object
        """
        if not violations:
            logger.warning("No violations provided, generating no-incident report")
            return self._generate_no_incident_report(metadata)
        
        # Format violation details
        violation_details = self._format_violations(violations)
        
        # Select template
        template = custom_template or self.REPORT_TEMPLATES[format]
        
        # Build prompt
        prompt = template.format(
            violation_details=violation_details,
            location=metadata.location,
            timestamp=metadata.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            site_id=metadata.site_id or "N/A",
            inspector_id=metadata.inspector_id or "Automated System"
        )
        
        # Generate report text
        logger.info("Generating report with LLM...")
        report_text = self.provider.generate(prompt)
        
        # Extract recommendations
        recommendations = self._extract_recommendations(report_text, violations)
        
        # Create report object
        report = IncidentReport(
            report_id=self._generate_report_id(),
            title=f"Safety Incident Report - {metadata.location}",
            text=report_text,
            metadata=metadata,
            violations=violations,
            recommendations=recommendations,
            format=format,
            generated_at=datetime.now()
        )
        
        logger.success(f"Report generated: {report.report_id}")
        return report
    
    def _format_violations(self, violations: List[Dict]) -> str:
        """Format violations into readable text."""
        formatted = []
        
        for i, violation in enumerate(violations, 1):
            formatted.append(f"""
Violation #{i}:
- Type: {violation.get('type', 'unknown')}
- Description: {violation.get('description', 'N/A')}
- Severity: {violation.get('severity', 'unknown').upper()}
- OSHA Standard: {violation.get('osha_standard', 'N/A')}
- Detection Confidence: {violation.get('confidence', 0):.2%}
""")
        
        return "\n".join(formatted)
    
    def _extract_recommendations(
        self,
        report_text: str,
        violations: List[Dict]
    ) -> List[str]:
        """Extract actionable recommendations from report."""
        recommendations = []
        
        # Default recommendations based on violation types
        violation_types = {v.get('type') for v in violations}
        
        if 'no_helmet' in violation_types:
            recommendations.extend([
                "Provide mandatory hard hat training",
                "Install PPE requirement signage at entry points",
                "Implement daily PPE inspection protocols"
            ])
        
        if 'no_vest' in violation_types:
            recommendations.extend([
                "Ensure adequate supply of safety vests",
                "Enforce high-visibility clothing policy",
                "Review site visibility requirements"
            ])
        
        # Try to extract from report text (simple keyword matching)
        keywords = ['must', 'should', 'required', 'recommend', 'necessary']
        lines = report_text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                cleaned = line.strip('- •*').strip()
                if cleaned and len(cleaned) > 20:
                    recommendations.append(cleaned)
        
        return list(set(recommendations))[:10]  # Deduplicate and limit
    
    @staticmethod
    def _generate_report_id() -> str:
        """Generate unique report ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"RPT-{timestamp}"
    
    def _generate_no_incident_report(self, metadata: ReportMetadata) -> IncidentReport:
        """Generate report when no violations detected."""
        report_text = f"""
WORKPLACE SAFETY INSPECTION REPORT

Inspection Location: {metadata.location}
Inspection Date/Time: {metadata.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
Inspector: {metadata.inspector_id or 'Automated System'}

FINDINGS: NO VIOLATIONS DETECTED

This automated inspection revealed no Personal Protective Equipment (PPE) violations 
at the time of assessment. All personnel observed were in compliance with applicable 
safety regulations.

OBSERVATIONS:
- All personnel wearing required hard hats
- Safety vests properly worn and visible
- No immediate safety hazards identified

RECOMMENDATION:
Continue current safety protocols and maintain regular inspections.

Status: COMPLIANT
"""
        
        return IncidentReport(
            report_id=self._generate_report_id(),
            title=f"Safety Inspection - {metadata.location} - NO VIOLATIONS",
            text=report_text,
            metadata=metadata,
            violations=[],
            recommendations=["Maintain current safety standards"],
            format=ReportFormat.FORMAL,
            generated_at=datetime.now()
        )


def create_report_generator(config: Optional[Dict] = None) -> ReportGenerator:
    """
    Factory function to create report generator.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Initialized ReportGenerator
    """
    config = config or {}
    
    return ReportGenerator(
        provider=config.get("provider", "ollama"),
        model=config.get("model"),
        temperature=config.get("temperature", 0.3),
        api_key=config.get("api_key"),
        base_url=config.get("base_url")
    )
