"""
Pytest configuration and fixtures for Merlin tests.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [
            {
                "text": '{"agent_type": "ingestion", "action": "ingest_text", "confidence": 0.9, "reasoning": "Text content detected"}'
            }
        ]
    }


@pytest.fixture
def mock_strands_agent():
    """Mock Strands Agent."""
    mock_agent = Mock()
    mock_agent.structured_output.return_value = Mock(
        agent_type="ingestion",
        action="ingest_text",
        confidence=0.9,
        reasoning="Test routing decision"
    )
    return mock_agent


@pytest.fixture
def sample_content():
    """Sample content for testing."""
    return {
        "title": "Test Article",
        "summary": "This is a test summary of the article content.",
        "tags": ["test", "article", "sample"],
        "content_type": "article",
        "key_insights": ["Test insight 1", "Test insight 2"]
    }


@pytest.fixture
def sample_note():
    """Sample note data for testing."""
    return {
        "id": 1,
        "title": "Test Note",
        "content": "This is test content for a note.",
        "summary": "Test summary",
        "tags": ["test", "note"],
        "embedding": [0.1, 0.2, 0.3] * 128,  # 384-dimensional embedding
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def sample_url():
    """Sample URL for testing."""
    return "https://example.com/test-article"


@pytest.fixture
def sample_text():
    """Sample text content for testing."""
    return """
    This is a test article about machine learning and artificial intelligence.
    It covers various topics including neural networks, deep learning, and natural language processing.
    The article discusses the current state of AI research and future prospects.
    """


@pytest.fixture
def mock_database_session():
    """Mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_note_model():
    """Mock Note model."""
    note = Mock()
    note.id = 1
    note.title = "Test Note"
    note.content = "Test content"
    note.summary = "Test summary"
    note.tags = ["test", "note"]
    note.embedding = [0.1, 0.2, 0.3] * 128
    note.created_at = "2024-01-01T00:00:00"
    return note


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Ensure we're in test mode
    os.environ["TESTING"] = "true"
    yield
    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def temp_db():
    """Temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    return [0.1, 0.2, 0.3] * 128  # 384-dimensional vector


@pytest.fixture
def mock_similarity_score():
    """Mock similarity score."""
    return 0.85


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def mock_router_agent():
    """Mock router agent for testing."""
    agent = Mock()
    agent.classify_input.return_value = {
        'agent_type': 'ingestion',
        'action': 'ingest_text',
        'input_data': {'content': 'test content'},
        'confidence': 0.9,
        'reasoning': 'Test routing'
    }
    agent.validate_routing.return_value = True
    return agent


@pytest.fixture
def mock_ingestion_agent():
    """Mock ingestion agent for testing."""
    agent = Mock()
    agent.process_ingestion.return_value = {
        'success': True,
        'result': {'note': {'id': 1, 'title': 'Test Note'}},
        'message': 'Successfully processed'
    }
    return agent


@pytest.fixture
def mock_query_agent():
    """Mock query agent for testing."""
    agent = Mock()
    agent.process_query.return_value = {
        'success': True,
        'result': {'results': [{'id': 1, 'title': 'Test Result'}]},
        'message': 'Query processed'
    }
    return agent


@pytest.fixture
def mock_summarization_agent():
    """Mock summarization agent for testing."""
    agent = Mock()
    agent.process_summarization.return_value = {
        'success': True,
        'result': {'generated_summary': 'Test summary'},
        'message': 'Summary generated'
    }
    return agent
