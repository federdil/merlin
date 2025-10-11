"""
Integration tests for the Merlin API.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app


class TestAPIIntegration:
    """Integration tests for the complete API workflow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == "Merlin - Personal Knowledge Curator API"
        assert data['version'] == "2.0.0"
        assert data['architecture'] == "Strands Agents"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == "healthy"
        assert data['service'] == "merlin-api"

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.ingestion_agent')
    @patch('app.agents.tools.database_ops.add_note')
    @patch('app.agents.tools.embedding.generate_embedding')
    def test_complete_url_ingestion_workflow(self, mock_generate_embedding, mock_add_note,
                                           mock_ingestion_agent, mock_router_agent, client):
        """Test complete URL ingestion workflow."""
        # Mock the router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'ingestion',
            'action': 'ingest_url',
            'input_data': {
                'url': 'https://example.com',
                'title': 'Example Title',
                'content': 'Example content'
            },
            'confidence': 0.95,
            'reasoning': 'URL detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock the ingestion agent
        mock_ingestion_agent.process_ingestion.return_value = {
            'success': True,
            'result': {
                'note': {
                    'id': 1,
                    'title': 'Example Title',
                    'summary': 'Generated summary',
                    'tags': ['example', 'test'],
                    'created_at': '2024-01-01T00:00:00'
                },
                'similar_notes': []
            },
            'message': 'Successfully ingested URL'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "https://example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['agent_type'] == 'ingestion'
        assert data['action'] == 'ingest_url'
        assert 'note' in data['result']

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.query_agent')
    @patch('app.agents.tools.search.semantic_search')
    def test_complete_search_workflow(self, mock_semantic_search, mock_query_agent, 
                                    mock_router_agent, client):
        """Test complete search workflow."""
        # Mock the router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'query',
            'action': 'search',
            'input_data': {
                'query': 'What is machine learning?',
                'search_type': 'semantic'
            },
            'confidence': 0.9,
            'reasoning': 'Question detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock the query agent
        mock_query_agent.process_query.return_value = {
            'success': True,
            'result': {
                'query': 'What is machine learning?',
                'search_type': 'semantic',
                'results': [
                    {
                        'id': 1,
                        'title': 'Machine Learning Basics',
                        'summary': 'Introduction to ML concepts',
                        'tags': ['machine learning', 'ai']
                    }
                ]
            },
            'message': 'Found 1 results'
        }
        
        response = client.post(
            "/api/v1/process",
            json={"input_text": "What is machine learning?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['agent_type'] == 'query'
        assert data['action'] == 'search'
        assert 'results' in data['result']

    @patch('app.routes.process_input.router_agent')
    @patch('app.routes.process_input.summarization_agent')
    def test_complete_summarization_workflow(self, mock_summarization_agent, 
                                           mock_router_agent, client):
        """Test complete summarization workflow."""
        # Mock the router agent
        mock_router_agent.classify_input.return_value = {
            'agent_type': 'summarization',
            'action': 'summarize_existing',
            'input_data': {
                'content': 'This is a long article about AI...'
            },
            'confidence': 0.8,
            'reasoning': 'Summarization request detected'
        }
        mock_router_agent.validate_routing.return_value = True
        
        # Mock the summarization agent
        mock_summarization_agent.process_summarization.return_value = {
            'success': True,
            'result': {
                'generated_summary': 'This article discusses AI concepts...',
                'generated_tags': ['ai', 'technology'],
                'key_insights': ['AI is transforming industries']
            },
            'message': 'Summary generated successfully'
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
        assert 'generated_summary' in data['result']

    def test_agents_info_endpoint(self, client):
        """Test agents info endpoint."""
        response = client.get("/api/v1/agents/info")
        
        assert response.status_code == 200
        data = response.json()
        assert 'router_agent' in data
        assert 'ingestion_agent' in data
        assert 'query_agent' in data
        assert 'summarization_agent' in data

    def test_agent_capabilities_endpoint(self, client):
        """Test agent capabilities endpoint."""
        response = client.get("/api/v1/agents/ingestion/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        assert 'name' in data
        assert 'description' in data
        assert 'supported_actions' in data

    def test_agent_capabilities_invalid_agent(self, client):
        """Test agent capabilities endpoint with invalid agent."""
        response = client.get("/api/v1/agents/invalid_agent/capabilities")
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail']

    def test_validate_input_endpoint(self, client):
        """Test validate input endpoint."""
        response = client.post(
            "/api/v1/agents/ingestion/validate",
            json={
                "action": "ingest_text",
                "input_data": {"content": "Test content"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'valid' in data
        assert 'agent_type' in data

    def test_validate_input_invalid_agent(self, client):
        """Test validate input endpoint with invalid agent."""
        response = client.post(
            "/api/v1/agents/invalid_agent/validate",
            json={"action": "test", "input_data": {}}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()['detail']

    def test_process_input_empty_string(self, client):
        """Test processing empty input string."""
        with patch('app.routes.process_input.router_agent') as mock_router_agent:
            mock_router_agent.classify_input.return_value = {
                'agent_type': 'query',
                'action': 'empty_input',
                'input_data': {'original_input': ''},
                'confidence': 1.0,
                'reasoning': 'Empty input'
            }
            mock_router_agent.validate_routing.return_value = True
            
            with patch('app.routes.process_input.query_agent') as mock_query_agent:
                mock_query_agent.process_query.return_value = {
                    'success': True,
                    'result': {'recent_notes': []},
                    'message': 'Empty input handled'
                }
                
                response = client.post(
                    "/api/v1/process",
                    json={"input_text": ""}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                assert data['agent_type'] == 'query'
                assert data['action'] == 'empty_input'

    def test_process_input_long_text(self, client):
        """Test processing long text input."""
        long_text = "This is a very long text " * 100
        
        with patch('app.routes.process_input.router_agent') as mock_router_agent:
            mock_router_agent.classify_input.return_value = {
                'agent_type': 'ingestion',
                'action': 'ingest_text',
                'input_data': {'content': long_text},
                'confidence': 0.85,
                'reasoning': 'Long text content'
            }
            mock_router_agent.validate_routing.return_value = True
            
            with patch('app.routes.process_input.ingestion_agent') as mock_ingestion_agent:
                mock_ingestion_agent.process_ingestion.return_value = {
                    'success': True,
                    'result': {'note': {'id': 1, 'title': 'Long Text'}},
                    'message': 'Long text processed'
                }
                
                response = client.post(
                    "/api/v1/process",
                    json={"input_text": long_text}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['success'] is True
                assert data['agent_type'] == 'ingestion'
