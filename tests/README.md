# Tests

This folder contains unit tests and integration tests for EmailCraft AI.

## Running Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=agents --cov=database --cov=utils

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

## Test Structure

- `test_agents.py` - Tests for AI agents
- `test_api.py` - Tests for API endpoints
- `test_database.py` - Tests for database operations (add as needed)
- `test_utils.py` - Tests for utility functions (add as needed)

## Writing Tests

Follow pytest conventions:

- Test files should start with `test_`
- Test functions should start with `test_`
- Use descriptive test names
- Use fixtures for common setup

Example:

```python
def test_email_generation():
    """Test email generation with valid input."""
    agent = GenerationAgent()
    result = agent.generate(...)
    assert result is not None
```
