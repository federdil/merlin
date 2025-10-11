# 🧪 Merlin Testing Guide

## Overview

This guide covers the comprehensive testing suite for the Merlin Personal Knowledge Curator with Strands Agents architecture.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_runner.py           # Comprehensive test runner
├── unit/                    # Unit tests
│   ├── tools/              # Tool unit tests
│   │   ├── test_content_fetcher.py
│   │   ├── test_tagging.py
│   │   └── test_embedding.py
│   ├── agents/             # Agent unit tests
│   │   ├── test_strands_router_agent.py
│   │   └── test_strands_ingestion_agent.py
│   └── api/                # API unit tests
│       └── test_process_input.py
└── integration/            # Integration tests
    └── test_api_integration.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/test_runner.py

# Run with coverage
python tests/test_runner.py --coverage

# Run specific test types
python tests/test_runner.py --type unit
python tests/test_runner.py --type integration
python tests/test_runner.py --type tools
python tests/test_runner.py --type agents
python tests/test_runner.py --type api
```

### Using pytest directly

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/unit/tools/test_content_fetcher.py
pytest tests/unit/agents/test_strands_router_agent.py

# Run with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf
```

### Test Runner Options

```bash
# Check test environment
python tests/test_runner.py --check

# Generate comprehensive report
python tests/test_runner.py --report

# Run with verbose output
python tests/test_runner.py --verbose

# Run with coverage report
python tests/test_runner.py --coverage
```

## Test Categories

### Unit Tests

**Tools Tests** (`tests/unit/tools/`)
- `test_content_fetcher.py`: URL content extraction and input parsing
- `test_tagging.py`: Tag normalization and keyword extraction
- `test_embedding.py`: Vector embedding generation and similarity computation

**Agent Tests** (`tests/unit/agents/`)
- `test_strands_router_agent.py`: Intelligent input classification and routing
- `test_strands_ingestion_agent.py`: AI-powered content processing and analysis

**API Tests** (`tests/unit/api/`)
- `test_process_input.py`: Unified API endpoint functionality

### Integration Tests

**API Integration** (`tests/integration/`)
- `test_api_integration.py`: End-to-end API workflow testing

## Test Features

### Fixtures and Mocks

The test suite includes comprehensive fixtures in `conftest.py`:

- **Mock Anthropic API responses**
- **Mock Strands Agent instances**
- **Sample content and note data**
- **Database session mocks**
- **Embedding and similarity mocks**
- **FastAPI test client**

### Coverage

Tests provide comprehensive coverage of:

- ✅ **Tool Functions**: All utility functions with edge cases
- ✅ **Agent Logic**: Routing, ingestion, and processing workflows
- ✅ **API Endpoints**: Request/response handling and error cases
- ✅ **Integration**: Complete user workflows
- ✅ **Error Handling**: Exception scenarios and fallbacks

### Test Scenarios

#### Content Fetcher Tests
- URL content extraction (success/failure)
- Input type classification (URL/text/empty)
- Error handling for invalid URLs

#### Tagging Tests
- Tag normalization and deduplication
- Keyword extraction from content
- Tag merging and validation

#### Embedding Tests
- Vector generation and similarity computation
- Batch processing consistency
- Edge cases with empty/invalid inputs

#### Router Agent Tests
- Input classification with Strands framework
- Fallback routing when Claude is unavailable
- Confidence scoring and reasoning

#### Ingestion Agent Tests
- URL and text content processing
- AI-powered analysis with Claude
- Database storage and error handling

#### API Tests
- Unified endpoint functionality
- Agent routing and delegation
- Request/response validation
- Error handling and status codes

#### Integration Tests
- Complete user workflows
- Multi-agent interactions
- End-to-end API testing

## Test Configuration

### Environment Variables

Tests use the following environment variables:

```bash
TESTING=true
ANTHROPIC_API_KEY=test-api-key
DATABASE_URL=sqlite:///:memory:
```

### Pytest Configuration

Configuration is in `pytest.ini`:

- **Test discovery patterns**
- **Output formatting**
- **Coverage settings**
- **Markers for test categorization**
- **Timeout settings**

## Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from app.module.function import function_to_test

class TestFunctionName:
    """Test class for specific functionality."""
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = function_to_test("input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            function_to_test("invalid_input")
    
    @patch('app.module.external_dependency')
    def test_with_mock(self, mock_dependency):
        """Test with mocked dependencies."""
        mock_dependency.return_value = "mocked_value"
        result = function_to_test("input")
        assert result == "expected_with_mock"
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Group related tests** in classes
3. **Use fixtures** for common test data
4. **Mock external dependencies** to ensure isolated testing
5. **Test both success and failure scenarios**
6. **Include edge cases** and boundary conditions
7. **Use parametrized tests** for multiple similar test cases

### Adding New Test Files

1. Create test file in appropriate directory
2. Follow naming convention: `test_*.py`
3. Import necessary fixtures from `conftest.py`
4. Add comprehensive test cases
5. Update documentation if needed

## Continuous Integration

### GitHub Actions (Recommended)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/test_runner.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

```yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: python tests/test_runner.py --type unit
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure project root is in Python path
2. **Missing Dependencies**: Install all requirements including test dependencies
3. **Mock Failures**: Check mock setup and patching paths
4. **Database Issues**: Use in-memory SQLite for tests

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s --tb=long

# Run specific test with debug
pytest -v -s tests/unit/tools/test_content_fetcher.py::TestFetchUrlContent::test_fetch_url_content_success
```

### Performance Testing

```bash
# Run tests with timing information
pytest --durations=10

# Profile slow tests
pytest --profile
```

## Coverage Reports

### HTML Coverage Report

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Coverage Targets

- **Overall Coverage**: > 90%
- **Critical Paths**: > 95%
- **Tool Functions**: > 95%
- **Agent Logic**: > 90%
- **API Endpoints**: > 95%

## Test Data

### Sample Data

Tests use consistent sample data defined in fixtures:

- **Sample URLs**: `https://example.com/test-article`
- **Sample Content**: Machine learning and AI text
- **Sample Notes**: Structured note objects with embeddings
- **Sample Tags**: Technology-related tags

### Mock Data

All external dependencies are mocked:

- **Anthropic API**: Mocked Claude responses
- **Strands Framework**: Mocked agent instances
- **Database**: In-memory SQLite with mock sessions
- **Embeddings**: Mocked vector generation

## Maintenance

### Regular Tasks

1. **Update test data** when adding new features
2. **Review coverage reports** and add tests for uncovered code
3. **Update mocks** when external APIs change
4. **Refactor tests** to maintain readability
5. **Add integration tests** for new workflows

### Test Quality Metrics

- **Test Coverage**: Monitor coverage percentages
- **Test Execution Time**: Keep tests fast (< 30 seconds total)
- **Test Reliability**: Ensure tests pass consistently
- **Test Maintainability**: Keep tests simple and readable

---

**Happy Testing!** 🧪✨

For questions or issues with the test suite, please refer to the test code documentation or create an issue in the repository.
