"""
Unit tests for StrandsIngestionAgent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.strands_ingestion_agent import StrandsIngestionAgent, ContentAnalysis


class TestStrandsIngestionAgent:
    """Test StrandsIngestionAgent class."""

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_initialization(self, mock_agent_class, mock_model_class):
        """Test agent initialization."""
        # Mock the model and agent
        mock_model = Mock()
        mock_agent = Mock()
        mock_model_class.return_value = mock_model
        mock_agent_class.return_value = mock_agent
        
        agent = StrandsIngestionAgent()
        
        assert agent.name == "StrandsIngestionAgent"
        assert agent.description == "AI-powered content ingestion using Strands and Claude"
        mock_model_class.assert_called_once()
        mock_agent_class.assert_called_once()

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_process_ingestion_unknown_action(self, mock_agent_class, mock_model_class):
        """Test processing with unknown action."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        result = agent.process_ingestion("unknown_action", {})
        
        assert result['success'] is False
        assert 'Unknown ingestion action' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_process_ingestion_exception(self, mock_agent_class, mock_model_class):
        """Test processing with exception."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        # Mock the _ingest_text method to raise an exception
        with patch.object(agent, '_ingest_text', side_effect=Exception("Test error")):
            result = agent.process_ingestion("ingest_text", {})
        
        assert result['success'] is False
        assert 'Ingestion failed: Test error' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.fetch_url_content')
    def test_ingest_url_success(self, mock_fetch_url, mock_agent_class, mock_model_class):
        """Test successful URL ingestion."""
        mock_fetch_url.return_value = ("Test Title", "Test Content")
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        
        with patch.object(agent, '_process_content_with_strands') as mock_process:
            mock_process.return_value = {'success': True, 'result': {}, 'message': 'Success'}
            
            input_data = {'url': 'https://example.com'}
            result = agent._ingest_url(input_data)
            
            assert result['success'] is True
            mock_fetch_url.assert_called_once_with('https://example.com')
            mock_process.assert_called_once()

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.fetch_url_content')
    def test_ingest_url_no_url(self, mock_fetch_url, mock_agent_class, mock_model_class):
        """Test URL ingestion without URL."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        result = agent._ingest_url({})
        
        assert result['success'] is False
        assert 'URL is required' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.fetch_url_content')
    def test_ingest_url_fetch_failure(self, mock_fetch_url, mock_agent_class, mock_model_class):
        """Test URL ingestion with fetch failure."""
        mock_fetch_url.return_value = (None, None)
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        result = agent._ingest_url({'url': 'https://invalid.com'})
        
        assert result['success'] is False
        assert 'Failed to extract content' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_ingest_text_success(self, mock_agent_class, mock_model_class):
        """Test successful text ingestion."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        
        with patch.object(agent, '_process_content_with_strands') as mock_process:
            mock_process.return_value = {'success': True, 'result': {}, 'message': 'Success'}
            
            input_data = {'content': 'Test content', 'title': 'Test Title'}
            result = agent._ingest_text(input_data)
            
            assert result['success'] is True
            mock_process.assert_called_once()

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_ingest_text_no_content(self, mock_agent_class, mock_model_class):
        """Test text ingestion without content."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        result = agent._ingest_text({})
        
        assert result['success'] is False
        assert 'Content is required' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.normalize_tags')
    @patch('app.agents.strands_ingestion_agent.generate_embedding')
    @patch('app.agents.strands_ingestion_agent.add_note')
    @patch('app.agents.strands_ingestion_agent.find_similar_notes')
    def test_process_content_with_strands_success(self, mock_find_similar, mock_add_note, 
                                                 mock_generate_embedding, mock_normalize_tags,
                                                 mock_agent_class, mock_model_class):
        """Test successful content processing with Strands."""
        # Mock the agent and its structured output
        mock_agent = Mock()
        mock_analysis = Mock()
        mock_analysis.title = "AI Generated Title"
        mock_analysis.summary = "AI generated summary"
        mock_analysis.tags = ["ai", "test"]
        mock_analysis.content_type = "article"
        mock_analysis.key_insights = ["Insight 1", "Insight 2"]
        mock_agent.structured_output.return_value = mock_analysis
        
        mock_agent_class.return_value = mock_agent
        
        # Mock other dependencies
        mock_normalize_tags.return_value = ["ai", "test"]
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        mock_note = Mock()
        mock_note.id = 1
        mock_note.title = "AI Generated Title"
        mock_note.summary = "AI generated summary"
        mock_note.tags = ["ai", "test"]
        mock_note.embedding = [0.1, 0.2, 0.3]
        # Mock created_at as a datetime object that has isoformat method
        mock_created_at = Mock()
        mock_created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_note.created_at = mock_created_at
        mock_add_note.return_value = mock_note
        
        mock_find_similar.return_value = []
        
        agent = StrandsIngestionAgent()
        result = agent._process_content_with_strands(
            title=None,
            content="Test content",
            source_type="text",
            source_url=None,
            original_input="Test content"
        )
        
        assert result['success'] is True
        assert 'AI Generated Title' in result['message']
        mock_agent.structured_output.assert_called_once()
        mock_add_note.assert_called_once()

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.normalize_tags')
    @patch('app.agents.strands_ingestion_agent.generate_embedding')
    @patch('app.agents.strands_ingestion_agent.add_note')
    @patch('app.agents.strands_ingestion_agent.find_similar_notes')
    def test_process_content_with_strands_fallback(self, mock_find_similar, mock_add_note, mock_generate_embedding,
                                                 mock_normalize_tags, mock_agent_class, mock_model_class):
        """Test content processing with Strands fallback."""
        # Mock the agent to raise an exception
        mock_agent = Mock()
        mock_agent.structured_output.side_effect = Exception("Strands failed")
        mock_agent_class.return_value = mock_agent
        
        # Mock other dependencies
        mock_normalize_tags.return_value = []
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_find_similar.return_value = []
        
        mock_note = Mock()
        mock_note.id = 1
        mock_note.title = "Test content"[:80]
        mock_note.summary = "Test content"[:200]
        mock_note.tags = []
        mock_note.embedding = [0.1, 0.2, 0.3]
        # Mock created_at as a datetime object that has isoformat method
        mock_created_at = Mock()
        mock_created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_note.created_at = mock_created_at
        mock_add_note.return_value = mock_note
        
        agent = StrandsIngestionAgent()
        
        result = agent._process_content_with_strands(
            title=None,
            content="Test content",
            source_type="text",
            source_url=None,
            original_input="Test content"
        )
        
        assert result['success'] is True
        # Should use fallback processing
        mock_add_note.assert_called_once()

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.strands_ingestion_agent.normalize_tags')
    @patch('app.agents.strands_ingestion_agent.generate_embedding')
    @patch('app.agents.strands_ingestion_agent.add_note')
    def test_process_content_database_error(self, mock_add_note, mock_generate_embedding, mock_normalize_tags,
                                         mock_agent_class, mock_model_class):
        """Test content processing with database error."""
        mock_agent_class.return_value = Mock()
        mock_normalize_tags.return_value = ["test"]
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_add_note.side_effect = Exception("Database error")
        
        agent = StrandsIngestionAgent()
        
        result = agent._process_content_with_strands(
            title=None,
            content="Test content",
            source_type="text",
            source_url=None,
            original_input="Test content"
        )
        
        assert result['success'] is False
        assert 'Database storage failed' in result['error']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.tools.embedding.compute_similarity')
    def test_calculate_similarity_score_success(self, mock_compute_similarity, mock_agent_class, mock_model_class):
        """Test similarity score calculation success."""
        mock_agent_class.return_value = Mock()
        mock_compute_similarity.return_value = 0.85
        
        agent = StrandsIngestionAgent()
        
        result = agent._calculate_similarity_score([0.1, 0.2], [0.3, 0.4])
        
        assert result == 0.85

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    @patch('app.agents.tools.embedding.compute_similarity')
    def test_calculate_similarity_score_failure(self, mock_compute_similarity, mock_agent_class, mock_model_class):
        """Test similarity score calculation failure."""
        mock_agent_class.return_value = Mock()
        mock_compute_similarity.side_effect = Exception("Error")
        
        agent = StrandsIngestionAgent()
        
        result = agent._calculate_similarity_score([0.1, 0.2], [0.3, 0.4])
        
        assert result == 0.0

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_get_capabilities(self, mock_agent_class, mock_model_class):
        """Test getting agent capabilities."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        capabilities = agent.get_capabilities()
        
        assert capabilities['name'] == "StrandsIngestionAgent"
        assert capabilities['framework'] == 'Strands'
        assert capabilities['model'] == 'claude-3-5-haiku-20241022'
        assert 'intelligent_title_generation' in capabilities['ai_features']

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_validate_input_url(self, mock_agent_class, mock_model_class):
        """Test input validation for URL."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        
        # Valid URL input
        assert agent.validate_input("ingest_url", {'url': 'https://example.com'}) is True
        
        # Invalid URL input
        assert agent.validate_input("ingest_url", {'url': ''}) is False
        assert agent.validate_input("ingest_url", {}) is False

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_validate_input_text(self, mock_agent_class, mock_model_class):
        """Test input validation for text."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        
        # Valid text input
        assert agent.validate_input("ingest_text", {'content': 'Test content'}) is True
        
        # Invalid text input
        assert agent.validate_input("ingest_text", {'content': ''}) is False
        assert agent.validate_input("ingest_text", {}) is False

    @patch('app.agents.strands_ingestion_agent.AnthropicModel')
    @patch('app.agents.strands_ingestion_agent.Agent')
    def test_validate_input_unknown_action(self, mock_agent_class, mock_model_class):
        """Test input validation for unknown action."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsIngestionAgent()
        assert agent.validate_input("unknown_action", {}) is False


class TestContentAnalysis:
    """Test ContentAnalysis Pydantic model."""

    def test_content_analysis_valid(self):
        """Test valid content analysis."""
        analysis = ContentAnalysis(
            title="Test Article",
            summary="This is a test summary of the article.",
            tags=["test", "article"],
            content_type="article",
            key_insights=["Insight 1", "Insight 2"]
        )
        
        assert analysis.title == "Test Article"
        assert analysis.summary == "This is a test summary of the article."
        assert analysis.tags == ["test", "article"]
        assert analysis.content_type == "article"
        assert analysis.key_insights == ["Insight 1", "Insight 2"]

    def test_content_analysis_minimal(self):
        """Test minimal content analysis."""
        analysis = ContentAnalysis(
            title="Title",
            summary="Summary",
            tags=[],
            content_type="text",
            key_insights=[]
        )
        
        assert analysis.title == "Title"
        assert analysis.summary == "Summary"
        assert analysis.tags == []
        assert analysis.content_type == "text"
        assert analysis.key_insights == []
