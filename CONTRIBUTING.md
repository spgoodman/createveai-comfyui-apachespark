# Contributing to CreateveAI Apache Spark Nodes

Thank you for your interest in contributing to the CreateveAI Apache Spark nodes for ComfyUI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)
- [Style Guide](#style-guide)

## Code of Conduct

This project follows a Code of Conduct that all contributors are expected to adhere to. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/createveai-comfyui-apachespark.git
   cd createveai-comfyui-apachespark
   ```

3. Set up development environment:
   ```bash
   # Start Docker environment
   docker-compose up -d
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

## Development Environment

### Prerequisites
- Python 3.10+
- Java 11+
- Docker and Docker Compose
- Git

### IDE Setup

#### VSCode
1. Install extensions:
   - Python
   - Pylance
   - Docker
   - YAML

2. Configure settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black"
   }
   ```

#### PyCharm
1. Install plugins:
   - Docker integration
   - Pyspark

2. Configure:
   - Set Python interpreter
   - Enable auto-formatting with black
   - Set line length to 88

## Making Changes

### Branching Strategy

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Keep branches focused:
   - One feature/fix per branch
   - Keep changes minimal and focused
   - Regularly sync with main

### Coding Guidelines

1. Follow PEP 8 style guide
2. Use type hints
3. Write docstrings for all public APIs
4. Keep functions focused and small
5. Add appropriate error handling

### Adding New Nodes

1. Create node class:
   ```python
   from .base import Node
   
   class NewNode(Node):
       CATEGORY = "CreateveAI/Apache Spark"
       RETURN_TYPES = ("DATASET",)
       RETURN_NAMES = ("output_dataset",)
       
       @classmethod
       def INPUT_TYPES(cls):
           return {
               "required": {
                   "param1": ("STRING", {})
               }
           }
       
       def execute(self, param1: str) -> tuple:
           # Implementation
           pass
   ```

2. Register node in `__init__.py`:
   ```python
   from .new_node import NewNode
   
   NODE_CLASS_MAPPINGS = {
       "NewNode": NewNode
   }
   ```

3. Add tests in `tests/`:
   ```python
   def test_new_node():
       node = NewNode()
       result = node.execute("test")
       assert result is not None
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_new_node.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

1. Test file structure:
   ```python
   import pytest
   from src.new_node import NewNode
   
   @pytest.fixture
   def node():
       return NewNode()
   
   def test_basic_functionality(node):
       result = node.execute("test")
       assert isinstance(result, tuple)
   
   def test_error_handling(node):
       with pytest.raises(ValueError):
           node.execute(None)
   ```

2. Test categories:
   - Unit tests for individual components
   - Integration tests for node interactions
   - End-to-end tests for workflows

## Submitting Changes

1. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create Pull Request:
   - Use clear title and description
   - Reference any related issues
   - Include test results
   - Add documentation updates

## Documentation

### Types of Documentation

1. Code Documentation:
   - Docstrings for classes and functions
   - Inline comments for complex logic
   - Type hints for parameters and returns

2. API Documentation:
   - Update API reference
   - Add examples
   - Document breaking changes

3. User Documentation:
   - Update README.md
   - Add/update guides
   - Include examples

### Documentation Style

1. Docstrings:
   ```python
   def function_name(param1: str, param2: int) -> bool:
       """
       Brief description of function.
       
       Args:
           param1: Description of param1
           param2: Description of param2
           
       Returns:
           Description of return value
           
       Raises:
           ValueError: Description of when this error occurs
       """
       pass
   ```

2. README updates:
   - Keep information current
   - Include new features
   - Update requirements

## Style Guide

### Python Style

1. Follow PEP 8
2. Use black for formatting
3. Maximum line length: 88 characters
4. Use type hints
5. Use f-strings for string formatting

### Commit Messages

Follow Conventional Commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance

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
- [ ] Tests added/updated
- [ ] All tests passing

## Documentation
- [ ] Documentation updated
- [ ] Examples added/updated

## Additional Notes
Any additional information
```

## Questions?

Feel free to:
- Open an issue
- Join our Discord
- Contact maintainers

Thank you for contributing!
