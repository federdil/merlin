"""
Strands-compatible Ingestion Agent for Merlin.
Uses the actual Strands framework with Claude for content processing.
"""

import os
from typing import Dict, Any, Optional, List
from strands import Agent
from strands.models.anthropic import AnthropicModel
from app.agents.tools.content_fetcher import fetch_url_content
from app.agents.tools.tagging import normalize_tags
from app.agents.tools.embedding import generate_embedding
from app.agents.tools.database_ops import add_note
from app.agents.tools.search import find_similar_notes
from pydantic import BaseModel, Field


class ContentAnalysis(BaseModel):
    """Structured output for content analysis."""
    title: str = Field(description="Generated or extracted title for the content")
    summary: str = Field(description="Concise summary (120-180 words)")
    tags: List[str] = Field(description="5-10 semantic tags (lowercase, no punctuation)")
    content_type: str = Field(description="Type of content: 'article', 'note', 'research', 'tutorial', etc.")
    key_insights: List[str] = Field(description="3-5 key insights or takeaways")


class StrandsIngestionAgent:
    """
    Ingestion agent using Strands framework for intelligent content processing.
    """
    
    def __init__(self):
        self.name = "StrandsIngestionAgent"
        self.description = "AI-powered content ingestion using Strands and Claude"
        
        # Initialize Claude model via Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            },
            max_tokens=800,
            model_id="claude-3-5-haiku-20241022",  # Using PRIMARY_MODEL
            params={
                "temperature": 0.2,
            }
        )
        
        # Create Strands agent for content analysis
        self.agent = Agent(
            model=self.model,
            system_prompt=self._get_analysis_prompt()
        )
    
    def _get_analysis_prompt(self) -> str:
        """Get the system prompt for content analysis."""
        return """You are Merlin's intelligent content analyzer. Your job is to analyze content and extract meaningful information.

For any content provided:
1. Generate a clear, descriptive title
2. Create a concise summary (120-180 words) that captures the main points
3. Extract 5-10 semantic tags that represent key concepts (lowercase, no punctuation)
4. Identify the content type (article, note, research, tutorial, news, etc.)
5. Highlight 3-5 key insights or takeaways

Be thoughtful and accurate in your analysis. Focus on the most important information that would help someone quickly understand the content."""
    
    def process_ingestion(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process ingestion requests using Strands framework.
        
        Args:
            action: Type of ingestion action ('ingest_url', 'ingest_text')
            input_data: Input data containing content and metadata
            
        Returns:
            Dict containing the result of the ingestion process
        """
        try:
            if action == 'ingest_url':
                return self._ingest_url(input_data)
            elif action == 'ingest_text':
                return self._ingest_text(input_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown ingestion action: {action}',
                    'result': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ingestion failed: {str(e)}',
                'result': None
            }
    
    def _ingest_url(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest content from a URL using Strands analysis."""
        url = input_data.get('url')
        if not url:
            return {
                'success': False,
                'error': 'URL is required for URL ingestion',
                'result': None
            }
        
        # Fetch content from URL
        title, content = fetch_url_content(url)
        
        if not content:
            return {
                'success': False,
                'error': 'Failed to extract content from URL',
                'result': None
            }
        
        # Process the content with Strands
        return self._process_content_with_strands(
            title=title,
            content=content,
            source_type='url',
            source_url=url,
            original_input=input_data.get('original_input', url)
        )
    
    def _ingest_text(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest content from text using Strands analysis."""
        content = input_data.get('content')
        if not content:
            return {
                'success': False,
                'error': 'Content is required for text ingestion',
                'result': None
            }
        
        title = input_data.get('title')
        
        # Process the content with Strands
        return self._process_content_with_strands(
            title=title,
            content=content,
            source_type='text',
            source_url=None,
            original_input=input_data.get('original_input', content)
        )
    
    def _process_content_with_strands(self, title: Optional[str], content: str, 
                                    source_type: str, source_url: Optional[str], 
                                    original_input: str) -> Dict[str, Any]:
        """Process content through the full ingestion pipeline using Strands."""
        
        # Use Strands agent for intelligent content analysis
        try:
            analysis = self.agent.structured_output(
                ContentAnalysis,
                f"""
Content to analyze:
Title: {title or 'Not provided'}
Content: {content[:4000]}  # Limit content length for Claude
                """
            )
            
            # Use Claude's analysis
            final_title = analysis.title
            summary = analysis.summary
            tags = analysis.tags
            content_type = analysis.content_type
            key_insights = analysis.key_insights
            
        except Exception as e:
            print(f"Strands analysis failed, using fallback: {e}")
            # Fallback to simple processing
            final_title = title or content[:80]
            summary = content[:200]
            tags = []
            content_type = 'text'
            key_insights = []
        
        # Normalize tags
        normalized_tags = normalize_tags(tags) if tags else []
        
        # Generate embedding
        embedding = generate_embedding(content)
        
        # Store in database
        try:
            db_note = add_note(
                title=final_title,
                content=content,
                summary=summary,
                tags=normalized_tags,
                embedding=embedding
            )
            
            # Find similar notes
            similar_notes = find_similar_notes(db_note.id, top_k=3)
            
            # Prepare result
            result = {
                'note': {
                    'id': db_note.id,
                    'title': db_note.title,
                    'summary': db_note.summary,
                    'tags': normalize_tags(db_note.tags),
                    'created_at': db_note.created_at.isoformat(),
                    'source_type': source_type,
                    'source_url': source_url
                },
                'analysis': {
                    'content_type': content_type,
                    'key_insights': key_insights,
                    'processing_method': 'strands_claude'
                },
                'similar_notes': [
                    {
                        'id': note.id,
                        'title': note.title,
                        'summary': note.summary,
                        'tags': normalize_tags(note.tags),
                        'similarity_score': self._calculate_similarity_score(db_note.embedding, note.embedding)
                    }
                    for note in similar_notes
                ],
                'processing_metadata': {
                    'content_length': len(content),
                    'summary_length': len(summary),
                    'tag_count': len(normalized_tags),
                    'embedding_dimension': len(embedding),
                    'insights_count': len(key_insights)
                }
            }
            
            return {
                'success': True,
                'result': result,
                'message': f'Successfully ingested {source_type} with AI analysis: {final_title}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Database storage failed: {str(e)}',
                'result': None
            }
    
    def _calculate_similarity_score(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity score between two embeddings."""
        try:
            from app.agents.tools.embedding import compute_similarity
            score = compute_similarity(embedding1, embedding2)
            # Convert numpy types to Python native types for JSON serialization
            return float(score)
        except:
            return 0.0
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'framework': 'Strands',
            'model': 'claude-3-5-haiku-20241022',
            'supported_actions': ['ingest_url', 'ingest_text'],
            'input_types': ['url', 'text'],
            'output_format': 'structured_note_with_ai_analysis',
            'ai_features': [
                'intelligent_title_generation',
                'contextual_summarization',
                'semantic_tag_extraction',
                'content_type_classification',
                'key_insights_extraction'
            ],
            'tools_used': [
                'content_fetcher',
                'tagging',
                'embedding',
                'database_ops',
                'search'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'ingest_url':
            return 'url' in input_data and bool(input_data.get('url'))
        elif action == 'ingest_text':
            return 'content' in input_data and bool(input_data.get('content'))
        return False
