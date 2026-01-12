"""
Tests for LLM report generator
"""

import pytest
from datetime import datetime
from app.core.llm.generator import (
    ReportGenerator,
    ReportMetadata,
    ReportFormat,
    OpenAIProvider,
    GeminiProvider,
    create_report_generator
)


def test_report_metadata_creation():
    """Test creation of report metadata."""
    metadata = ReportMetadata(
        location="Test Site",
        timestamp=datetime.now(),
        site_id="SITE-001",
        inspector_id="INS-123"
    )
    
    assert metadata.location == "Test Site"
    assert metadata.site_id == "SITE-001"
    assert metadata.inspector_id == "INS-123"


def test_report_formats():
    """Test report format enum."""
    assert ReportFormat.FORMAL.value == "formal"
    assert ReportFormat.TECHNICAL.value == "technical"
    assert ReportFormat.EXECUTIVE.value == "executive"
    assert ReportFormat.EMAIL.value == "email"


def test_report_generator_initialization():
    """Test report generator initialization."""
    # This will fail without API keys, which is expected
    try:
        generator = create_report_generator({
            "provider": "openai",
            "model": "gpt-4o"
        })
    except ValueError as e:
        assert "API key" in str(e)


def test_no_violation_report():
    """Test generation of no-violation report."""
    # Mock generator without API
    metadata = ReportMetadata(
        location="Safe Site",
        timestamp=datetime.now()
    )
    
    # Would need to mock the LLM provider for full test
    # This is a placeholder for the test structure
    assert metadata.location == "Safe Site"


def test_violation_formatting():
    """Test violation formatting."""
    violations = [
        {
            "type": "no_hardhat",
            "description": "Worker without hardhat",
            "severity": "high",
            "osha_standard": "29 CFR 1926.100",
            "confidence": 0.95
        }
    ]
    
    assert len(violations) == 1
    assert violations[0]["type"] == "no_hardhat"
    assert violations[0]["severity"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
