"""
Query Agent for Merlin - Handles search queries and information retrieval.
"""

from typing import Dict, Any, Optional, List
from app.agents.tools.search import (
    semantic_search, 
    search_by_content, 
    hybrid_search, 
    search_by_tags,
    get_recent_notes,
    find_similar_notes
)
from app.agents.tools.database_ops import get_note_by_id, get_note_statistics
from app.agents.tools.embedding import generate_embedding


class QueryAgent:
    """
    Agent responsible for handling search queries and information retrieval.
    """
    
    def __init__(self):
        self.name = "QueryAgent"
        self.description = "Handles search queries and information retrieval"
    
    def process_query(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process query requests based on action type.
        
        Args:
            action: Type of query action ('search', 'find_similar', 'get_recent', 'empty_input')
            input_data: Input data containing query parameters
            
        Returns:
            Dict containing the search results
        """
        try:
            if action == 'search':
                return self._handle_search(input_data)
            elif action == 'find_similar':
                return self._handle_find_similar(input_data)
            elif action == 'get_recent':
                return self._handle_get_recent(input_data)
            elif action == 'empty_input':
                return self._handle_empty_input(input_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown query action: {action}',
                    'result': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Query processing failed: {str(e)}',
                'result': None
            }
    
    def _handle_search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search queries."""
        query = input_data.get('query', '').strip()
        if not query:
            return {
                'success': False,
                'error': 'Search query is required',
                'result': None
            }
        
        search_type = input_data.get('search_type', 'semantic')
        top_k = input_data.get('top_k', 5)
        
        try:
            if search_type == 'semantic':
                results = semantic_search(query, top_k)
            elif search_type == 'text':
                results = search_by_content(query, top_k)
            elif search_type == 'hybrid':
                results = hybrid_search(query, top_k=top_k)
            elif search_type == 'tags':
                tags = [tag.strip() for tag in query.split(',')]
                results = search_by_tags(tags, top_k)
            else:
                results = semantic_search(query, top_k)
            
            # Format results
            formatted_results = []
            for note in results:
                formatted_results.append({
                    'id': note.id,
                    'title': note.title,
                    'summary': note.summary,
                    'tags': note.tags or [],
                    'created_at': note.created_at.isoformat(),
                    'content_preview': note.content[:200] + '...' if len(note.content) > 200 else note.content
                })
            
            return {
                'success': True,
                'result': {
                    'query': query,
                    'search_type': search_type,
                    'results': formatted_results,
                    'total_results': len(formatted_results),
                    'search_metadata': {
                        'query_length': len(query),
                        'search_type': search_type
                    }
                },
                'message': f'Found {len(formatted_results)} results for "{query}"'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Search failed: {str(e)}',
                'result': None
            }
    
    def _handle_find_similar(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests to find similar notes."""
        note_id = input_data.get('note_id')
        if not note_id:
            return {
                'success': False,
                'error': 'Note ID is required for finding similar notes',
                'result': None
            }
        
        top_k = input_data.get('top_k', 3)
        
        try:
            similar_notes = find_similar_notes(note_id, top_k)
            
            # Get the original note
            original_note = get_note_by_id(note_id)
            if not original_note:
                return {
                    'success': False,
                    'error': f'Note with ID {note_id} not found',
                    'result': None
                }
            
            # Format results
            formatted_results = []
            for note in similar_notes:
                formatted_results.append({
                    'id': note.id,
                    'title': note.title,
                    'summary': note.summary,
                    'tags': note.tags or [],
                    'created_at': note.created_at.isoformat(),
                    'similarity_score': self._calculate_similarity_score(original_note.embedding, note.embedding)
                })
            
            return {
                'success': True,
                'result': {
                    'original_note': {
                        'id': original_note.id,
                        'title': original_note.title,
                        'summary': original_note.summary
                    },
                    'similar_notes': formatted_results,
                    'total_similar': len(formatted_results)
                },
                'message': f'Found {len(formatted_results)} similar notes'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Finding similar notes failed: {str(e)}',
                'result': None
            }
    
    def _handle_get_recent(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests to get recent notes."""
        limit = input_data.get('limit', 10)
        
        try:
            recent_notes = get_recent_notes(limit)
            
            # Format results
            formatted_results = []
            for note in recent_notes:
                formatted_results.append({
                    'id': note.id,
                    'title': note.title,
                    'summary': note.summary,
                    'tags': note.tags or [],
                    'created_at': note.created_at.isoformat()
                })
            
            return {
                'success': True,
                'result': {
                    'recent_notes': formatted_results,
                    'total_recent': len(formatted_results),
                    'limit': limit
                },
                'message': f'Retrieved {len(formatted_results)} recent notes'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Getting recent notes failed: {str(e)}',
                'result': None
            }
    
    def _handle_empty_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle empty input by showing recent notes and statistics."""
        try:
            # Get recent notes
            recent_notes = get_recent_notes(5)
            
            # Get statistics
            stats = get_note_statistics()
            
            # Format recent notes
            formatted_notes = []
            for note in recent_notes:
                formatted_notes.append({
                    'id': note.id,
                    'title': note.title,
                    'summary': note.summary,
                    'tags': note.tags or [],
                    'created_at': note.created_at.isoformat()
                })
            
            return {
                'success': True,
                'result': {
                    'recent_notes': formatted_notes,
                    'statistics': stats,
                    'suggestion': 'Try searching for specific topics or paste a URL to add new content'
                },
                'message': 'Showing recent notes and statistics'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Handling empty input failed: {str(e)}',
                'result': None
            }
    
    def _calculate_similarity_score(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate similarity score between two embeddings."""
        try:
            from app.agents.tools.embedding import compute_similarity
            return compute_similarity(embedding1, embedding2)
        except:
            return 0.0
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about agent capabilities."""
        return {
            'name': self.name,
            'description': self.description,
            'supported_actions': ['search', 'find_similar', 'get_recent', 'empty_input'],
            'search_types': ['semantic', 'text', 'hybrid', 'tags'],
            'output_format': 'search_results_with_metadata',
            'tools_used': [
                'search',
                'database_ops',
                'embedding'
            ]
        }
    
    def validate_input(self, action: str, input_data: Dict[str, Any]) -> bool:
        """Validate input data for the specified action."""
        if action == 'search':
            return 'query' in input_data and input_data['query']
        elif action == 'find_similar':
            return 'note_id' in input_data and input_data['note_id']
        elif action in ['get_recent', 'empty_input']:
            return True
        return False
