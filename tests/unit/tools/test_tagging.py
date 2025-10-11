"""
Unit tests for tagging tool.
"""

import pytest
from app.agents.tools.tagging import (
    normalize_tags,
    extract_keywords_from_content,
    merge_tags
)


class TestNormalizeTags:
    """Test normalize_tags function."""

    def test_normalize_tags_list_of_strings(self):
        """Test normalizing a list of strings."""
        tags = ["Machine Learning", "AI", "  Python  ", "Data Science"]
        result = normalize_tags(tags)
        
        expected = ["machine learning", "ai", "python", "data science"]
        assert result == expected

    def test_normalize_tags_with_punctuation(self):
        """Test normalizing tags with punctuation."""
        tags = ["Machine-Learning!", "AI/ML", "Python 3.0", "Data-Science?"]
        result = normalize_tags(tags)
        
        expected = ["machine-learning", "ai/ml", "python 30", "data-science"]
        assert result == expected

    def test_normalize_tags_empty_list(self):
        """Test normalizing empty list."""
        result = normalize_tags([])
        assert result == []

    def test_normalize_tags_none(self):
        """Test normalizing None input."""
        result = normalize_tags(None)
        assert result == []

    def test_normalize_tags_removes_duplicates(self):
        """Test that normalization removes duplicates."""
        tags = ["Python", "python", "PYTHON", "Java", "java"]
        result = normalize_tags(tags)
        
        expected = ["python", "java"]
        assert result == expected

    def test_normalize_tags_filters_short_tags(self):
        """Test that normalization filters out short tags."""
        tags = ["AI", "ML", "Python", "a", "b", "Machine Learning"]
        result = normalize_tags(tags)
        
        # Should keep AI, ML, Python, Machine Learning (length > 1)
        expected = ["ai", "ml", "python", "machine learning"]
        assert result == expected

    def test_normalize_tags_string_input(self):
        """Test normalizing string input."""
        tags = "Python, Machine Learning, AI"
        result = normalize_tags(tags)
        
        expected = ["python", "machine learning", "ai"]
        assert result == expected

    def test_normalize_tags_json_array_string(self):
        """Test normalizing JSON array string."""
        tags = '["Python", "Machine Learning", "AI"]'
        result = normalize_tags(tags)
        
        expected = ["python", "machine learning", "ai"]
        assert result == expected

    def test_normalize_tags_postgres_array_string(self):
        """Test normalizing PostgreSQL array string."""
        tags = '{"Python","Machine Learning","AI"}'
        result = normalize_tags(tags)
        
        expected = ["python", "machine learning", "ai"]
        assert result == expected


class TestExtractKeywordsFromContent:
    """Test extract_keywords_from_content function."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        content = "Machine learning is a subset of artificial intelligence. Python is commonly used for data science."
        result = extract_keywords_from_content(content, max_tags=5)
        
        # Should extract meaningful keywords
        assert len(result) <= 5
        assert all(len(tag) > 1 for tag in result)

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered out."""
        content = "The machine learning algorithm processes data and generates predictions."
        result = extract_keywords_from_content(content)
        
        # Should not contain stop words like "the", "and", "of"
        stop_words = ["the", "and", "of", "is", "a", "are"]
        for tag in result:
            assert tag not in stop_words

    def test_extract_keywords_empty_content(self):
        """Test keyword extraction from empty content."""
        result = extract_keywords_from_content("")
        assert result == []

    def test_extract_keywords_short_content(self):
        """Test keyword extraction from short content."""
        content = "AI ML"
        result = extract_keywords_from_content(content)
        
        # Should handle short content gracefully
        assert isinstance(result, list)

    def test_extract_keywords_max_tags_limit(self):
        """Test that max_tags limit is respected."""
        content = "Machine learning artificial intelligence data science python programming algorithm neural network deep learning natural language processing computer vision robotics automation"
        result = extract_keywords_from_content(content, max_tags=3)
        
        assert len(result) <= 3

    def test_extract_keywords_case_insensitive(self):
        """Test that keyword extraction is case insensitive."""
        content = "Machine Learning MACHINE LEARNING machine learning"
        result = extract_keywords_from_content(content)
        
        # Should treat same words in different cases as the same keyword
        assert len(set(result)) == 2  # 'machine' and 'learning'
        assert 'machine' in result
        assert 'learning' in result


class TestMergeTags:
    """Test merge_tags function."""

    def test_merge_tags_basic(self):
        """Test basic tag merging."""
        existing_tags = ["python", "machine learning"]
        new_tags = ["ai", "data science"]
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "machine learning", "ai", "data science"]
        assert result == expected

    def test_merge_tags_removes_duplicates(self):
        """Test that merging removes duplicates."""
        existing_tags = ["python", "machine learning", "ai"]
        new_tags = ["ai", "python", "deep learning"]
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "machine learning", "ai", "deep learning"]
        assert result == expected

    def test_merge_tags_max_total_limit(self):
        """Test that max_total limit is respected."""
        existing_tags = ["tag1", "tag2", "tag3", "tag4", "tag5"]
        new_tags = ["tag6", "tag7", "tag8", "tag9", "tag10", "tag11"]
        result = merge_tags(existing_tags, new_tags, max_total=8)
        
        assert len(result) <= 8

    def test_merge_tags_empty_existing(self):
        """Test merging with empty existing tags."""
        existing_tags = []
        new_tags = ["python", "ai", "ml"]
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "ai", "ml"]
        assert result == expected

    def test_merge_tags_empty_new(self):
        """Test merging with empty new tags."""
        existing_tags = ["python", "ai", "ml"]
        new_tags = []
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "ai", "ml"]
        assert result == expected

    def test_merge_tags_normalizes_tags(self):
        """Test that merging normalizes tags."""
        existing_tags = ["Python", "  AI  ", "Machine Learning!"]
        new_tags = ["Data Science", "ML", "Deep Learning"]
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "ai", "machine learning", "data science", "ml", "deep learning"]
        assert result == expected

    def test_merge_tags_case_insensitive_deduplication(self):
        """Test case-insensitive deduplication."""
        existing_tags = ["Python", "AI", "Machine Learning"]
        new_tags = ["python", "ai", "ML"]
        result = merge_tags(existing_tags, new_tags)
        
        expected = ["python", "ai", "machine learning", "ml"]
        assert result == expected
