"""
Summarization Agent for Merlin - Handles summarization requests and content analysis.
"""

from typing import Dict, Any, Optional, List
from app.agents.tools.summarize import summarize_and_tag, is_llm_available
from app.agents.tools.database_ops import get_note_by_id, search_notes_by_content
from app.agents.tools.search import semantic_search
from app.agents.tools.tagging import normalize_tags


class SummarizationAgent:
    """
    Agent responsible for handling summarization requests and content analysis.
    """
    
    def __init__(self):
        self.name = "SummarizationAgent"
        self.description = "Handles summarization requests and content analysis"
    
    def process_summarization(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process summarization requests based on action type.
        
        Args:
            action: Type of summarization action ('summarize_existing', 'generate_summary')
            input_data: Input data containing content or note references
            
        Returns:
            Dict containing the summarization result
        """
        try:
            if action == 'summarize_existing':
                return self._summarize_existing_content(input_data)
            elif action == 'generate_summary':
                return self._generate_summary(input_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown summarization action: {action}',
                    'result': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Summarization processing failed: {str(e)}',
                'result': None
            }
    
    def _summarize_existing_content(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize existing content in the knowledge base."""
        content = input_data.get('content', '').strip()
        if not content:
            return {
                'success': False,
                'error': 'Content is required for summarization',
                'result': None
            }
        
        try:
            # Generate summary and tags
            summary, tags = summarize_and_tag(content)
            
            # Normalize tags
            normalized_tags = normalize_tags(tags) if tags else []
            
            # Find related content in the knowledge base
            related_notes = semantic_search(content, top_k=3)
            
            # Format related notes
            formatted_related = []
            for note in related_notes:
                formatted_related.append({
                    'id': note.id,
                    'title': note.title,
                    'summary': note.summary,
                    'tags': note.tags or [],
                    'relevance_score': self._calculate_content_relevance(content, note.content)
                })
            
            return {
                'success': True,
                'result': {
                    'original_content': content,
                    'generated_summary': summary,
                    'generated_tags': normalized_tags,
                    'content_analysis': {
                        'content_length': len(content),
                        'summary_length': len(summary) if summary else 0,
                        'tag_count': len(normalized_tags),
                        'llm_available': is_llm_available()
                    },
                    'related_content': formatted_related
                },
                'message': 'Content summarized successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Summarization failed: {str(e)}',
                'result': None
            }
    
    def _generate_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary for specific content or note."""
        note_id = input_data.get('note_id')
        content = input_data.get('content')
        
        if not content and not note_id:
            return {
                'success': False,
                'error': 'Either content or note_id is required',
                'result': None
            }
        
        try:
            # Get content from note if note_id is provided
            if note_id and not content:
                note = get_note_by_id(note_id)
                if not note:
                    return {
                        'success': False,
                        'error': f'Note with ID {note_id} not found',
                        'result': None
                    }
                content = note.content
                original_title = note.title
            else:
                original_title = input_data.get('title', 'Untitled')
            
            # Generate new summary and tags
            new_summary, new_tags = summarize_and_tag(content)
            
            # Normalize tags
            normalized_tags = normalize_tags(new_tags) if new_tags else []
            
            # Analyze the content for key insights
            key_insights = self._extract_key_insights(content)
            
            return {
                'success': True,
                'result': {
                    'original_content': {
                        'title': original_title,
                        'content': content,
                        'note_id': note_id
                    },
                    'generated_summary': new_summary,
                    'generated_tags': normalized_tags,
                    'key_insights': key_insights,
                    'analysis_metadata': {
                        'content_length': len(content),
                        'summary_length': len(new_summary) if new_summary else 0,
                        'tag_count': len(normalized_tags),
                        'insight_count': len(key_insights),
                        'llm_available': is_llm_available()
                    }
                },
                'message': 'Summary generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Summary generation failed: {str(e)}',
                'result': None
            }
    
    def _calculate_content_relevance(self, query_content: str, note_content: str) -> float:
        """Calculate relevance score between query content and note content."""
        # Simple relevance calculation based on common words
        query_words = set(query_content.lower().split())
        note_words = set(note_content.lower().split())
        
        if not query_words or not note_words:
            return 0.0
        
        common_words = query_words.intersection(note_words)
        return len(common_words) / len(query_words.union(note_words))
    
    def _extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content."""
        # Simple insight extraction - in a real implementation, this could use more sophisticated NLP
        sentences = content.split('.')
        insights = []
        
        # Look for sentences with key indicators
        key_indicators = ['important', 'key', 'main', 'primary', 'significant', 'crucial', 'essential']
        
        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in key_indicators):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    insights.append(sentence)
        
        return insights[:3]  # Return top 3 insights
    
    def analyze_content_trends(self, limit: int = 20) -> Dict[str, Any]:
        """Analyze trends in the content of recent notes."""
        try:
            from app.agents.tools.database_ops import get_recent_notes
            
            recent_notes = get_recent_notes(limit)
            
            # Analyze tags
            all_tags = []
            for note in recent_notes:
                if note.tags:
                    all_tags.extend(note.tags)
            
            # Count tag frequency
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Get top tags
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Analyze content themes (simplified)
            theme_analysis = self._analyze_content_themes([note.content for note in recent_notes])
            
            return {
                'success': True,
                'result': {
                    'total_notes_analyzed': len(recent_notes),
                    'top_tags': [{'tag': tag, 'count': count} for tag, count in top_tags],
                    'theme_analysis': theme_analysis,
                    'analysis_metadata': {
                        'analysis_date': 'current',
                        'notes_analyzed': len(recent_notes)
                    }
                },
                'message': f'Analyzed trends in {len(recent_notes)} recent notes'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Content trend analysis failed: {str(e)}',
                'result': None
            }
    
    def _analyze_content_themes(self, contents: List[str]) -> Dict[str, Any]:
        """Analyze themes in content (simplified implementation)."""
        # This is a simplified theme analysis
        # In a real implementation, you might use topic modeling or other NLP techniques
        
        all_text = ' '.join(contents).lower()
        
        # Simple keyword-based theme detection
        themes = {
            'technology': ['tech', 'software', 'programming', 'ai', 'machine learning', 'data'],
            'business': ['business', 'company', 'market', 'revenue', 'profit', 'strategy'],
            'science': ['research', 'study', 'experiment', 'theory', 'hypothesis', 'analysis'],
            'education': ['learn', 'teach', 'education', 'course', 'student', 'knowledge']
        }
        
        theme_scores = {}
        for theme, keywords in themes.items():
            score = sum(all_text.count(keyword) for keyword in keywords)
            theme_scores[theme] = score
        
        # Get top themes
        top_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'primary_themes': [theme for theme, score in top_themes if score > 0][:3],
            'theme_scores': theme_scores
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'supported_actions': ['summarize_existing', 'generate_summary', 'analyze_trends'],
            'input_types': ['content', 'note_id'],
            'output_format': 'summary_with_analysis',
            'tools_used': [
                'summarize',
                'database_ops',
                'search',
                'tagging'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'summarize_existing':
            return 'content' in input_data and input_data['content']
        elif action == 'generate_summary':
            return ('content' in input_data and input_data['content']) or ('note_id' in input_data and input_data['note_id'])
        return False
