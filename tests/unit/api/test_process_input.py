"""
Unit tests for process_input API endpoint.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.routes.process_input import ProcessInputRequest, ProcessInputResponse


class TestProcessInputAPI:
    """Test process input API endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.ingestion_agent')
    def test_process_input_success(self, mock_ingestion_agent, mock_router_agent, client):
        """Test successful input processing."""
        # Mock router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'ingestion',
            'action': 'ingest_text',
            'input_data': {'content': 'Test content'},
            'confidence': 0.9,
            'reasoning': 'Text content detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock ingestion agent
        mock_ingestion_agent.process_ingestion.return_value = {
            'success': True,
            'result': {'note': {'id': 1, 'title': 'Test Note'}},
            'message': 'Successfully processed'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "This is test content"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['agent_type'] == 'ingestion'
        assert data['action'] == 'ingest_text'
        assert data['message'] == 'Successfully processed'

    @patch('app.routes.process_input.router_agent')
    def test_process_input_routing_failure(self, mock_router_agent, client):
        """Test input processing with routing failure."""
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'invalid',
            'action': 'invalid_action',
            'input_data': {},
            'confidence': 0.5
        }
        mock_router_agent.validate_routing.return_value = False
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "Test input"}
        )
        
        assert response.status_code == 400
        assert "Invalid routing result" in response.json()['detail']

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.ingestion_agent')
    def test_process_input_agent_failure(self, mock_ingestion_agent, mock_router_agent, client):
        """Test input processing with agent failure."""
        # Mock router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'ingestion',
            'action': 'ingest_text',
            'input_data': {'content': 'Test content'},
            'confidence': 0.9,
            'reasoning': 'Text content detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock ingestion agent failure
        mock_ingestion_agent.process_ingestion.return_value = {
            'success': False,
            'error': 'Processing failed'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "This is test content"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert data['error'] == 'Processing failed'

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.query_agent')
    def test_process_input_query_agent(self, mock_query_agent, mock_router_agent, client):
        """Test input processing with query agent."""
        # Mock router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'query',
            'action': 'search',
            'input_data': {'query': 'What is AI?'},
            'confidence': 0.9,
            'reasoning': 'Question detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock query agent
        mock_query_agent.process_query.return_value = {
            'success': True,
            'result': {'results': [{'id': 1, 'title': 'Test Result'}]},
            'message': 'Query processed'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "What is artificial intelligence?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['agent_type'] == 'query'
        assert data['action'] == 'search'

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.summarization_agent')
    def test_process_input_summarization_agent(self, mock_summarization_agent, mock_router_agent, client):
        """Test input processing with summarization agent."""
        # Mock router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'summarization',
            'action': 'summarize_existing',
            'input_data': {'content': 'Summarize this content'},
            'confidence': 0.9,
            'reasoning': 'Summarization request detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock summarization agent
        mock_summarization_agent.process_summarization.return_value = {
            'success': True,
            'result': {'generated_summary': 'Test summary'},
            'message': 'Summary generated'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "Summarize this article about AI"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['agent_type'] == 'summarization'
        assert data['action'] == 'summarize_existing'

    def test_process_input_invalid_agent_type(self, client):
        """Test input processing with invalid agent type."""
        with patch('app.routes.process_input.router_agent') as mock_router_agent:
            mock_router_agent.classify_input.return_value = {
                'agent_type': 'invalid_agent',
                'action': 'some_action',
                'input_data': {},
                'confidence': 0.5,
                'reasoning': 'Test'
            }
            mock_router_agent.validate_routing.return_value = True
            
            response = client.post(
                "/api/v1/process",
                json={"input_text": "Test input"}
            )
            
            assert response.status_code == 400
            assert "Unknown agent type" in response.json()['detail']

    def test_process_input_internal_error(self, client):
        """Test input processing with internal error."""
        with patch('app.routes.process_input.router_agent') as mock_router_agent:
            mock_router_agent.classify_input.side_effect = Exception("Internal error")
            response = client.post(
                "/api/v1/process",
                json={"input_text": "Test input"}
            )
            
            assert response.status_code == 500
            assert "Internal server error" in response.json()['detail']

    def test_process_input_with_metadata(self, client):
        """Test input processing with metadata."""
        with patch('app.routes.process_input.router_agent') as mock_router_agent, \
             patch('app.routes.process_input.ingestion_agent') as mock_ingestion_agent:
            
            mock_router_agent.classify_input.return_value = {
                'agent_type': 'ingestion',
                'action': 'ingest_text',
                'input_data': {'content': 'Test content'},
                'confidence': 0.9,
                'reasoning': 'Text content detected'
            }
            mock_router_agent.validate_routing.return_value = True
            
            mock_ingestion_agent.process_ingestion.return_value = {
                'success': True,
                'result': {'note': {'id': 1, 'title': 'Test Note'}},
                'message': 'Successfully processed'
            }
            
            response = client.post(
                "/api/v1/process",
                json={
                    "input_text": "This is test content",
                    "user_id": "user123",
                    "metadata": {"source": "test"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['success'] is True
            assert data['processing_metadata']['user_id'] == 'user123'


class TestProcessInputRequest:
    """Test ProcessInputRequest model."""

    def test_process_input_request_basic(self):
        """Test basic request model."""
        request = ProcessInputRequest(input_text="Test input")
        
        assert request.input_text == "Test input"
        assert request.user_id is None
        assert request.metadata is None

    def test_process_input_request_with_metadata(self):
        """Test request model with metadata."""
        request = ProcessInputRequest(
            input_text="Test input",
            user_id="user123",
            metadata={"source": "test"}
        )
        
        assert request.input_text == "Test input"
        assert request.user_id == "user123"
        assert request.metadata == {"source": "test"}


class TestProcessInputResponse:
    """Test ProcessInputResponse model."""

    def test_process_input_response_success(self):
        """Test success response model."""
        response = ProcessInputResponse(
            success=True,
            agent_type="ingestion",
            action="ingest_text",
            result={"note": {"id": 1}},
            message="Success",
            processing_metadata={"confidence": 0.9}
        )
        
        assert response.success is True
        assert response.agent_type == "ingestion"
        assert response.action == "ingest_text"
        assert response.result == {"note": {"id": 1}}
        assert response.message == "Success"
        assert response.error is None

    def test_process_input_response_error(self):
        """Test error response model."""
        response = ProcessInputResponse(
            success=False,
            agent_type="ingestion",
            action="ingest_text",
            error="Processing failed",
            message="Failed"
        )
        
        assert response.success is False
        assert response.agent_type == "ingestion"
        assert response.action == "ingest_text"
        assert response.error == "Processing failed"
        assert response.result is None
