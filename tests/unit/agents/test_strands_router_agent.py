"""
Unit tests for StrandsRouterAgent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.strands_router_agent import StrandsRouterAgent, RoutingDecision


class TestStrandsRouterAgent:
    """Test StrandsRouterAgent class."""

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_initialization(self, mock_agent_class, mock_model_class):
        """Test agent initialization."""
        # Mock the model and agent
        mock_model = Mock()
        mock_agent = Mock()
        mock_model_class.return_value = mock_model
        mock_agent_class.return_value = mock_agent
        
        agent = StrandsRouterAgent()
        
        assert agent.name == "StrandsRouterAgent"
        assert agent.description == "Intelligent input classification using Strands and Claude"
        mock_model_class.assert_called_once()
        mock_agent_class.assert_called_once()

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_classify_input_empty(self, mock_agent_class, mock_model_class):
        """Test classification of empty input."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        
        agent = StrandsRouterAgent()
        result = agent.classify_input("")
        
        expected = {
            'agent_type': 'query',
            'action': 'empty_input',
            'input_data': {'original_input': ''},
            'confidence': 1.0,
            'reasoning': 'Empty input - showing recent notes'
        }
        assert result == expected

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    @patch('app.agents.strands_router_agent.extract_content_from_input')
    def test_classify_input_url(self, mock_extract, mock_agent_class, mock_model_class):
        """Test classification of URL input."""
        mock_agent = Mock()
        mock_routing_decision = Mock()
        mock_routing_decision.agent_type = 'ingestion'
        mock_routing_decision.action = 'ingest_url'
        mock_routing_decision.confidence = 0.95
        mock_routing_decision.reasoning = 'URL detected - route to ingestion'
        mock_agent.structured_output.return_value = mock_routing_decision
        mock_agent_class.return_value = mock_agent
        mock_extract.return_value = ("Test Title", "Test Content", "url")
        
        agent = StrandsRouterAgent()
        result = agent.classify_input("https://example.com")
        
        assert result['agent_type'] == 'ingestion'
        assert result['action'] == 'ingest_url'
        assert result['confidence'] == 0.95
        assert 'url' in result['input_data']

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    @patch('app.agents.strands_router_agent.extract_content_from_input')
    def test_classify_input_with_strands_success(self, mock_extract, mock_agent_class, mock_model_class):
        """Test successful classification using Strands."""
        # Mock the agent and its structured output
        mock_agent = Mock()
        mock_routing_decision = Mock()
        mock_routing_decision.agent_type = "ingestion"
        mock_routing_decision.action = "ingest_text"
        mock_routing_decision.confidence = 0.9
        mock_routing_decision.reasoning = "Text content detected"
        mock_agent.structured_output.return_value = mock_routing_decision
        
        mock_agent_class.return_value = mock_agent
        mock_extract.return_value = (None, "Test content", "text")
        
        agent = StrandsRouterAgent()
        result = agent.classify_input("This is test content")
        
        assert result['agent_type'] == "ingestion"
        assert result['action'] == "ingest_text"
        assert result['confidence'] == 0.9
        assert result['reasoning'] == "Text content detected"

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    @patch('app.agents.strands_router_agent.extract_content_from_input')
    def test_classify_input_with_strands_failure_fallback(self, mock_extract, mock_agent_class, mock_model_class):
        """Test fallback when Strands classification fails."""
        # Mock the agent to raise an exception
        mock_agent = Mock()
        mock_agent.structured_output.side_effect = Exception("Strands failed")
        mock_agent_class.return_value = mock_agent
        mock_extract.return_value = (None, "What is machine learning?", "text")
        
        agent = StrandsRouterAgent()
        result = agent.classify_input("What is machine learning?")
        
        # Should use fallback routing
        assert result['agent_type'] == 'query'
        assert result['action'] == 'search'
        assert result['confidence'] == 0.9

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    @patch('app.agents.strands_router_agent.extract_content_from_input')
    def test_classify_input_summarization_keywords(self, mock_extract, mock_agent_class, mock_model_class):
        """Test classification with summarization keywords."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_extract.return_value = (None, "Summarize this article about AI", "text")
        
        agent = StrandsRouterAgent()
        result = agent._fallback_routing("Summarize this article about AI", None, "Summarize this article about AI", "text")
        
        assert result['agent_type'] == 'summarization'
        assert result['action'] == 'summarize_existing'

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    @patch('app.agents.strands_router_agent.extract_content_from_input')
    def test_classify_input_question_keywords(self, mock_extract, mock_agent_class, mock_model_class):
        """Test classification with question keywords."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_extract.return_value = (None, "What is artificial intelligence?", "text")
        
        agent = StrandsRouterAgent()
        result = agent._fallback_routing("What is artificial intelligence?", None, "What is artificial intelligence?", "text")
        
        assert result['agent_type'] == 'query'
        assert result['action'] == 'search'

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_prepare_input_data_url(self, mock_agent_class, mock_model_class):
        """Test input data preparation for URL."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        result = agent._prepare_input_data(
            'ingestion', 'ingest_url', 'https://example.com',
            'Test Title', 'Test Content', 'url'
        )
        
        assert result['url'] == 'https://example.com'
        assert result['title'] == 'Test Title'
        assert result['content'] == 'Test Content'

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_prepare_input_data_text(self, mock_agent_class, mock_model_class):
        """Test input data preparation for text."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        result = agent._prepare_input_data(
            'ingestion', 'ingest_text', 'Test content',
            'Test Title', 'Test Content', 'text'
        )
        
        assert result['title'] == 'Test Title'
        assert result['content'] == 'Test Content'
        assert 'url' not in result

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_prepare_input_data_query(self, mock_agent_class, mock_model_class):
        """Test input data preparation for query."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        result = agent._prepare_input_data(
            'query', 'search', 'What is AI?',
            None, 'What is AI?', 'text'
        )
        
        assert result['query'] == 'What is AI?'
        assert result['search_type'] == 'semantic'

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_get_capabilities(self, mock_agent_class, mock_model_class):
        """Test getting agent capabilities."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        capabilities = agent.get_capabilities()
        
        assert capabilities['name'] == "StrandsRouterAgent"
        assert capabilities['framework'] == 'Strands'
        assert capabilities['model'] == 'claude-3-5-haiku-20241022'
        assert 'intelligent_input_classification' in capabilities['capabilities']

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_validate_routing_valid(self, mock_agent_class, mock_model_class):
        """Test routing validation with valid input."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        routing_result = {
            'agent_type': 'ingestion',
            'action': 'ingest_text',
            'input_data': {'content': 'test'},
            'confidence': 0.9
        }
        
        assert agent.validate_routing(routing_result) is True

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_validate_routing_invalid_agent_type(self, mock_agent_class, mock_model_class):
        """Test routing validation with invalid agent type."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        routing_result = {
            'agent_type': 'invalid_agent',
            'action': 'some_action',
            'input_data': {'content': 'test'},
            'confidence': 0.9
        }
        
        assert agent.validate_routing(routing_result) is False

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_validate_routing_invalid_confidence(self, mock_agent_class, mock_model_class):
        """Test routing validation with invalid confidence."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        routing_result = {
            'agent_type': 'ingestion',
            'action': 'ingest_text',
            'input_data': {'content': 'test'},
            'confidence': 1.5  # Invalid confidence > 1
        }
        
        assert agent.validate_routing(routing_result) is False

    @patch('app.agents.strands_router_agent.AnthropicModel')
    @patch('app.agents.strands_router_agent.Agent')
    def test_validate_routing_missing_fields(self, mock_agent_class, mock_model_class):
        """Test routing validation with missing fields."""
        mock_agent_class.return_value = Mock()
        
        agent = StrandsRouterAgent()
        routing_result = {
            'agent_type': 'ingestion',
            'action': 'ingest_text',
            # Missing input_data and confidence
        }
        
        assert agent.validate_routing(routing_result) is False


class TestRoutingDecision:
    """Test RoutingDecision Pydantic model."""

    def test_routing_decision_valid(self):
        """Test valid routing decision."""
        decision = RoutingDecision(
            agent_type="ingestion",
            action="ingest_text",
            confidence=0.9,
            reasoning="Test reasoning"
        )
        
        assert decision.agent_type == "ingestion"
        assert decision.action == "ingest_text"
        assert decision.confidence == 0.9
        assert decision.reasoning == "Test reasoning"

    def test_routing_decision_invalid_confidence(self):
        """Test routing decision with invalid confidence."""
        with pytest.raises(ValueError):
            RoutingDecision(
                agent_type="ingestion",
                action="ingest_text",
                confidence=1.5,  # Invalid > 1
                reasoning="Test reasoning"
            )

    def test_routing_decision_negative_confidence(self):
        """Test routing decision with negative confidence."""
        with pytest.raises(ValueError):
            RoutingDecision(
                agent_type="ingestion",
                action="ingest_text",
                confidence=-0.1,  # Invalid < 0
                reasoning="Test reasoning"
            )
