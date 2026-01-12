# Contributing to SiteGuard AI

Thank you for your interest in contributing to SiteGuard AI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and constructive
- Focus on what's best for the community
- Show empathy toward others
- Accept constructive criticism gracefully

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- CUDA-compatible GPU (optional but recommended)

### Setup Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/siteguard-ai.git
   cd siteguard-ai
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   make install
   # or
   pip install -r requirements.txt
   ```

4. **Download Models**
   ```bash
   python scripts/download_model.py
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Development Workflow

### Branch Naming Convention

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

Example: `feature/add-email-notifications`

### Workflow Steps

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Tests**
   ```bash
   make test
   ```

4. **Format Code**
   ```bash
   make format
   ```

5. **Lint Code**
   ```bash
   make lint
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add email notification feature"
   ```

   Follow conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `style:` - Formatting
   - `refactor:` - Code restructuring
   - `test:` - Adding tests
   - `chore:` - Maintenance

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: Maximum 120 characters
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google style docstrings
- **Type Hints**: Use type hints for function signatures

### Example

```python
from typing import List, Optional

def detect_violations(
    image_path: str,
    confidence: float = 0.5
) -> List[dict]:
    """
    Detect PPE violations in image.
    
    Args:
        image_path: Path to image file
        confidence: Minimum confidence threshold
        
    Returns:
        List of detected violations
        
    Raises:
        ValueError: If image cannot be loaded
    """
    pass
```

### Code Formatting

We use the following tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all formatters:
```bash
make format
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
└── e2e/           # End-to-end tests
```

### Writing Tests

1. **Use pytest**
   ```python
   import pytest
   
   def test_detector_initialization():
       detector = PPEDetector()
       assert detector is not None
   ```

2. **Use Fixtures**
   ```python
   @pytest.fixture
   def sample_image():
       return cv2.imread("test_image.jpg")
   
   def test_detection(sample_image):
       result = detector.detect(sample_image)
       assert len(result.detections) > 0
   ```

3. **Test Coverage**
   - Aim for >80% code coverage
   - Test edge cases and error conditions
   - Mock external dependencies (APIs, file I/O)

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage report
pytest --cov=app --cov-report=html
```

## Submitting Changes

### Pull Request Process

1. **Ensure Tests Pass**
   ```bash
   make pre-commit
   ```

2. **Update Documentation**
   - Update README if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

3. **Create Pull Request**
   - Use a clear, descriptive title
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Code Review Process

1. At least one approval required
2. All CI checks must pass
3. No merge conflicts
4. Maintainer will review within 48 hours

## Bug Reports

### Before Submitting

1. Check existing issues
2. Test with latest version
3. Verify it's reproducible

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the issue

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python Version: [e.g., 3.10.5]
- Package Version: [e.g., 1.0.0]

**Additional context**
Any other relevant information
```

## Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
Clear description of desired functionality

**Describe alternatives considered**
Other solutions you've considered

**Additional context**
Any other relevant information
```

## Development Tips

### Useful Commands

```bash
# Format and lint
make format lint

# Run specific test
pytest tests/unit/test_detector.py::test_specific_function -v

# Check test coverage
pytest --cov=app --cov-report=term-missing

# Profile code
python -m cProfile -o profile.stats script.py
```

### Debugging

1. **Use logging**
   ```python
   from loguru import logger
   logger.debug("Debugging information")
   ```

2. **Use debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Check logs**
   ```bash
   tail -f logs/siteguard_*.log
   ```

### Performance Optimization

- Profile code before optimizing
- Use vectorized operations (NumPy)
- Cache expensive computations
- Use appropriate data structures
- Consider async/await for I/O

## Documentation

### Docstring Example

```python
def generate_report(violations: List[Dict]) -> str:
    """
    Generate formatted safety incident report.
    
    This function uses an LLM to create a comprehensive report
    following OSHA standards and best practices.
    
    Args:
        violations: List of violation dictionaries containing:
            - type (str): Violation type identifier
            - description (str): Human-readable description
            - severity (str): Severity level (high/medium/low)
            - osha_standard (str): Applicable OSHA regulation
            
    Returns:
        Formatted report as string
        
    Raises:
        ValueError: If violations list is empty
        APIError: If LLM API call fails
        
    Example:
        >>> violations = [{"type": "no_helmet", ...}]
        >>> report = generate_report(violations)
        >>> print(report)
        SAFETY INCIDENT REPORT
        ...
    """
    pass
```

## Questions?

- Open an issue for technical questions
- Email: adibcom.as@gmail.com
- Check documentation: [docs/](docs/)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to SiteGuard AI! Your efforts help make workplace safety monitoring more accessible and effective.