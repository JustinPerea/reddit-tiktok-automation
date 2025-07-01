# Contributing to Reddit-to-TikTok Automation System

Thank you for your interest in contributing to this project! This document provides guidelines for contributing to the Reddit-to-TikTok Automation System.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/reddit-tiktok-automation.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## 🛠 Development Setup

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed on your system
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/reddit-tiktok-automation.git
cd reddit-tiktok-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running the Application
```bash
# Run the main application
python src/main.py

# Run tests
pytest

# Run linting
flake8 src/
black src/

# Run type checking
mypy src/
```

## 📁 Project Structure

```
reddit-tiktok-automation/
├── src/                    # Source code
│   ├── core/              # Core application logic
│   ├── api/               # API endpoints (Phase 2+)
│   ├── processors/        # Content processing modules
│   ├── generators/        # Video generation modules
│   ├── utils/             # Utility functions
│   └── config/            # Configuration management
├── tests/                 # Test files
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docs/                 # Documentation
├── assets/               # Static assets
├── output/               # Generated videos
├── config/               # Configuration files
└── scripts/              # Utility scripts
```

## 🔄 Development Workflow

### Branch Naming Convention
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Message Format
```
type(scope): brief description

Detailed description if necessary

- List specific changes
- Reference issues: Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 📝 Coding Standards

### Python Style Guide
- Follow PEP 8
- Use Black for code formatting: `black src/`
- Use flake8 for linting: `flake8 src/`
- Use mypy for type checking: `mypy src/`

### Code Quality
- Write docstrings for all functions and classes
- Use type hints for function parameters and return values
- Keep functions small and focused (max 50 lines)
- Use meaningful variable and function names
- Add comments for complex logic

### Example Code Style
```python
from typing import Optional, Dict, Any
from pathlib import Path

def process_reddit_content(
    content: str, 
    quality_threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Process Reddit content for video generation.
    
    Args:
        content: Raw Reddit post content
        quality_threshold: Minimum quality score (0.0-1.0)
        
    Returns:
        Processed content data or None if quality is too low
        
    Raises:
        ValueError: If content is empty or invalid
    """
    if not content.strip():
        raise ValueError("Content cannot be empty")
    
    # Process content logic here
    processed_data = {
        "text": content.strip(),
        "quality_score": calculate_quality_score(content),
        "word_count": len(content.split())
    }
    
    if processed_data["quality_score"] < quality_threshold:
        return None
        
    return processed_data
```

## 🧪 Testing

### Test Structure
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/e2e/`

### Writing Tests
```python
import pytest
from src.processors.content_processor import ContentProcessor

class TestContentProcessor:
    def test_process_valid_content(self):
        processor = ContentProcessor()
        content = "This is a valid Reddit story with enough content."
        
        result = processor.process(content)
        
        assert result is not None
        assert result["quality_score"] > 0.5
        assert result["word_count"] > 0
    
    def test_process_empty_content(self):
        processor = ContentProcessor()
        
        with pytest.raises(ValueError):
            processor.process("")
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_content_processor.py

# Run tests with verbose output
pytest -v
```

## 🔄 Pull Request Process

### Before Submitting
1. Ensure all tests pass: `pytest`
2. Run linting: `flake8 src/`
3. Format code: `black src/`
4. Update documentation if needed
5. Add tests for new functionality

### Pull Request Template
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
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process
1. Automated checks must pass
2. At least one code review required
3. Address all feedback
4. Maintainer approval required for merge

## 🐛 Reporting Issues

### Bug Reports
Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Relevant logs or error messages

### Feature Requests
Include:
- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any relevant examples or mockups

## 📚 Development Resources

### Useful Commands
```bash
# Setup pre-commit hooks
pre-commit install

# Update dependencies
pip-compile requirements.in

# Generate documentation
sphinx-build -b html docs/ docs/_build/

# Database migrations (when implemented)
alembic upgrade head
```

### Key Technologies
- **FastAPI**: Web framework for APIs
- **Pydantic**: Data validation and settings
- **SQLAlchemy**: Database ORM
- **FFmpeg**: Video processing
- **OpenAI/ElevenLabs**: Text-to-speech
- **Transformers**: AI/ML models

## 🆘 Getting Help

- Create an issue for bugs or feature requests
- Join our discussions for questions
- Check existing documentation in `docs/`
- Review the project roadmap in `README.md`

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

Thank you for contributing to the Reddit-to-TikTok Automation System! 🎉