"""
Unit tests for content_fetcher tool.
"""

import pytest
from unittest.mock import patch, Mock
from app.agents.tools.content_fetcher import (
    fetch_url_content,
    is_url,
    extract_content_from_input
)


class TestFetchUrlContent:
    """Test fetch_url_content function."""

    @patch('app.agents.tools.content_fetcher.trafilatura')
    def test_fetch_url_content_success(self, mock_trafilatura):
        """Test successful URL content fetching."""
        # Mock trafilatura responses
        mock_trafilatura.fetch_url.return_value = "Mock HTML content"
        mock_trafilatura.extract.return_value = "Extracted text content"
        
        url = "https://example.com/test"
        title, content = fetch_url_content(url)
        
        assert content == "Extracted text content"
        assert title is None  # trafilatura doesn't return title in plain-text mode
        mock_trafilatura.fetch_url.assert_called_once_with(url)
        mock_trafilatura.extract.assert_called_once()

    @patch('app.agents.tools.content_fetcher.trafilatura')
    def test_fetch_url_content_fetch_failure(self, mock_trafilatura):
        """Test URL fetching failure."""
        mock_trafilatura.fetch_url.return_value = None
        
        url = "https://invalid-url.com"
        title, content = fetch_url_content(url)
        
        assert title is None
        assert content is None
        mock_trafilatura.fetch_url.assert_called_once_with(url)
        mock_trafilatura.extract.assert_not_called()

    @patch('app.agents.tools.content_fetcher.trafilatura')
    def test_fetch_url_content_extract_failure(self, mock_trafilatura):
        """Test content extraction failure."""
        mock_trafilatura.fetch_url.return_value = "Mock HTML content"
        mock_trafilatura.extract.return_value = None
        
        url = "https://example.com/test"
        title, content = fetch_url_content(url)
        
        assert title is None
        assert content is None
        mock_trafilatura.fetch_url.assert_called_once_with(url)
        mock_trafilatura.extract.assert_called_once()


class TestIsUrl:
    """Test is_url function."""

    def test_is_url_valid_http(self):
        """Test valid HTTP URL."""
        assert is_url("http://example.com") is True

    def test_is_url_valid_https(self):
        """Test valid HTTPS URL."""
        assert is_url("https://example.com") is True

    def test_is_url_invalid(self):
        """Test invalid URL."""
        assert is_url("not a url") is False
        assert is_url("ftp://example.com") is False
        assert is_url("example.com") is False

    def test_is_url_empty(self):
        """Test empty string."""
        assert is_url("") is False

    def test_is_url_none(self):
        """Test None input."""
        assert is_url(None) is False


class TestExtractContentFromInput:
    """Test extract_content_from_input function."""

    @patch('app.agents.tools.content_fetcher.fetch_url_content')
    def test_extract_content_from_url(self, mock_fetch_url):
        """Test content extraction from URL."""
        mock_fetch_url.return_value = ("Test Title", "Test Content")
        
        input_text = "https://example.com/test"
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "url"
        assert title == "Test Title"
        assert content == "Test Content"
        mock_fetch_url.assert_called_once_with(input_text)

    @patch('app.agents.tools.content_fetcher.fetch_url_content')
    def test_extract_content_from_url_failure(self, mock_fetch_url):
        """Test URL content extraction failure."""
        mock_fetch_url.return_value = (None, None)
        
        input_text = "https://invalid-url.com"
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "url"
        assert title is None
        assert content is None

    def test_extract_content_from_text(self):
        """Test content extraction from text."""
        input_text = "This is some text content for testing."
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "text"
        assert title is None
        assert content == input_text

    def test_extract_content_from_empty(self):
        """Test content extraction from empty input."""
        input_text = ""
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "empty"
        assert title is None
        assert content is None

    def test_extract_content_from_whitespace(self):
        """Test content extraction from whitespace-only input."""
        input_text = "   \n\t   "
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "empty"
        assert title is None
        assert content is None

    def test_extract_content_strips_whitespace(self):
        """Test that content extraction strips whitespace."""
        input_text = "  This is test content.  "
        title, content, input_type = extract_content_from_input(input_text)
        
        assert input_type == "text"
        assert content == "This is test content."
